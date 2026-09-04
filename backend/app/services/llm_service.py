"""Multi-provider LLM client with tool-calling.

Provider order: Anthropic (if keyed) → OpenAI → Google. When only OpenAI is
configured, OpenAI is used first.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import structlog

from app.api.tools import get_available_tools
from app.config import Settings, get_settings
from app.services.tool_executor import ToolExecutor, dumps_tool_result

logger = structlog.get_logger(__name__)

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
DEFAULT_LLM_TIMEOUT_SECONDS = 60
MAX_TOOL_ROUNDS = 8


class LLMService:
    """Talks to configured LLM providers with a tool-calling loop."""

    def __init__(
        self,
        settings: Settings | None = None,
        tool_executor: ToolExecutor | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._timeout = self._settings.llm_timeout_seconds or DEFAULT_LLM_TIMEOUT_SECONDS
        self._tools = tool_executor or ToolExecutor()

    def load_prompt(self, name: str) -> str:
        """Load a system prompt from ``app/prompts/{name}.txt``."""
        path = PROMPTS_DIR / f"{name}.txt"
        if not path.is_file():
            raise FileNotFoundError(f"Prompt file not found: {path}. Add it under app/prompts/.")
        return path.read_text(encoding="utf-8")

    def available_providers(self) -> list[str]:
        """Return providers that have API keys configured, in preference order."""
        providers: list[str] = []
        if self._settings.anthropic_api_key:
            providers.append("anthropic")
        if self._settings.openai_api_key:
            providers.append("openai")
        if self._settings.google_api_key:
            providers.append("google")
        return providers

    async def complete_with_tools(
        self,
        *,
        prompt_name: str,
        user_message: str,
        tools: list[dict[str, Any]] | None = None,
    ) -> str:
        """Run a tool-calling loop against the first available provider.

        Returns:
            Final assistant text after tool calls complete.
        """
        system_prompt = self.load_prompt(prompt_name)
        tool_defs = tools if tools is not None else get_available_tools()
        providers = self.available_providers()
        if not providers:
            raise RuntimeError(
                "No LLM API keys configured. "
                "Set OPENAI_API_KEY (or ANTHROPIC_API_KEY / GOOGLE_API_KEY)."
            )

        last_error: Exception | None = None
        for provider in providers:
            for attempt in (1, 2):
                try:
                    logger.info(
                        "llm_provider_attempt",
                        provider=provider,
                        attempt=attempt,
                        prompt_name=prompt_name,
                        tool_count=len(tool_defs),
                    )
                    if provider == "openai":
                        return await self._openai_tool_loop(system_prompt, user_message, tool_defs)
                    if provider == "anthropic":
                        return await self._anthropic_tool_loop(
                            system_prompt, user_message, tool_defs
                        )
                    if provider == "google":
                        return await self._google_complete(system_prompt, user_message)
                except Exception as exc:  # noqa: BLE001
                    last_error = exc
                    logger.error(
                        "llm_provider_failed",
                        provider=provider,
                        attempt=attempt,
                        error=str(exc),
                    )
        raise RuntimeError(f"All LLM providers failed: {last_error}")

    async def synthesize_report_json(
        self,
        *,
        model_name: str,
        gathered: dict[str, Any],
    ) -> dict[str, Any]:
        """Ask the LLM to synthesize a structured analysis JSON from gathered tool data."""
        system = self.load_prompt("analyze")
        user = (
            f"Analyze the model `{model_name}` using the following tool results. "
            "Do not call tools. Return ONLY valid JSON with keys: "
            "analysis (string), recommendations (string[]), flaws (string[]), "
            "capabilities (object), summary (string). "
            "Never fabricate benchmark numbers.\n\n"
            f"TOOL_RESULTS:\n{json.dumps(gathered, default=str)[:120000]}"
        )
        providers = self.available_providers()
        if not providers:
            return self._fallback_synthesis(model_name, gathered)

        text = ""
        last_error: Exception | None = None
        for provider in providers:
            try:
                if provider == "openai":
                    text = await self._openai_chat(system, user)
                elif provider == "anthropic":
                    text = await self._anthropic_chat(system, user)
                else:
                    text = await self._google_complete(system, user)
                break
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                logger.error("synthesize_failed", provider=provider, error=str(exc))
        if not text:
            logger.warning("synthesize_fallback", error=str(last_error))
            return self._fallback_synthesis(model_name, gathered)
        parsed = self._extract_json(text)
        if parsed is None:
            return {
                **self._fallback_synthesis(model_name, gathered),
                "analysis": text.strip() or "Analysis completed from tool data.",
            }
        return parsed

    async def _openai_tool_loop(
        self,
        system_prompt: str,
        user_message: str,
        tool_defs: list[dict[str, Any]],
    ) -> str:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self._settings.openai_api_key, timeout=self._timeout)
        openai_tools = [self._to_openai_tool(t) for t in tool_defs]
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        for _ in range(MAX_TOOL_ROUNDS):
            response = await client.chat.completions.create(
                model=self._settings.openai_model,
                messages=messages,
                tools=openai_tools,
                tool_choice="auto",
                temperature=0.2,
            )
            choice = response.choices[0]
            message = choice.message
            messages.append(
                {
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in (message.tool_calls or [])
                    ]
                    if message.tool_calls
                    else None,
                }
            )
            # Clean None tool_calls for subsequent turns
            if messages[-1].get("tool_calls") is None:
                messages[-1].pop("tool_calls", None)

            if not message.tool_calls:
                return message.content or ""

            for tool_call in message.tool_calls:
                name = tool_call.function.name
                try:
                    arguments = json.loads(tool_call.function.arguments or "{}")
                except json.JSONDecodeError:
                    arguments = {}
                result = await self._tools.execute(name, arguments)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": dumps_tool_result(result),
                    }
                )

        return "Tool-calling loop reached maximum rounds without a final answer."

    async def _openai_chat(self, system_prompt: str, user_message: str) -> str:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self._settings.openai_api_key, timeout=self._timeout)
        response = await client.chat.completions.create(
            model=self._settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content or ""

    async def _anthropic_tool_loop(
        self,
        system_prompt: str,
        user_message: str,
        tool_defs: list[dict[str, Any]],
    ) -> str:
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=self._settings.anthropic_api_key, timeout=self._timeout)
        tools = [
            {
                "name": t["name"],
                "description": t["description"],
                "input_schema": t["input_schema"],
            }
            for t in tool_defs
        ]
        messages: list[dict[str, Any]] = [{"role": "user", "content": user_message}]

        for _ in range(MAX_TOOL_ROUNDS):
            response = await client.messages.create(
                model="claude-3-5-haiku-latest",
                max_tokens=4096,
                system=system_prompt,
                tools=tools,
                messages=messages,
            )
            if response.stop_reason == "tool_use":
                tool_results = []
                assistant_content = response.content
                messages.append({"role": "assistant", "content": assistant_content})
                for block in response.content:
                    if block.type != "tool_use":
                        continue
                    result = await self._tools.execute(block.name, dict(block.input))
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": dumps_tool_result(result),
                        }
                    )
                messages.append({"role": "user", "content": tool_results})
                continue

            texts = [b.text for b in response.content if getattr(b, "type", None) == "text"]
            return "\n".join(texts)

        return "Anthropic tool-calling loop reached maximum rounds."

    async def _anthropic_chat(self, system_prompt: str, user_message: str) -> str:
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=self._settings.anthropic_api_key, timeout=self._timeout)
        response = await client.messages.create(
            model="claude-3-5-haiku-latest",
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        texts = [b.text for b in response.content if getattr(b, "type", None) == "text"]
        return "\n".join(texts)

    async def _google_complete(self, system_prompt: str, user_message: str) -> str:
        import google.generativeai as genai

        genai.configure(api_key=self._settings.google_api_key)
        model = genai.GenerativeModel(
            "gemini-1.5-flash",
            system_instruction=system_prompt,
        )
        response = await model.generate_content_async(user_message)
        return response.text or ""

    @staticmethod
    def _to_openai_tool(tool: dict[str, Any]) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["input_schema"],
            },
        }

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any] | None:
        text = text.strip()
        try:
            data = json.loads(text)
            return data if isinstance(data, dict) else None
        except json.JSONDecodeError:
            match = re.search(r"\{[\s\S]*\}", text)
            if not match:
                return None
            try:
                data = json.loads(match.group(0))
                return data if isinstance(data, dict) else None
            except json.JSONDecodeError:
                return None

    @staticmethod
    def _fallback_synthesis(model_name: str, gathered: dict[str, Any]) -> dict[str, Any]:
        specs = gathered.get("specs") or {}
        capabilities = gathered.get("capabilities") or {}
        resources = gathered.get("resources") or {}
        competitors = (gathered.get("competitors") or {}).get("competitors") or []
        analysis_parts = [
            f"Evaluation of `{model_name}` based on live HuggingFace / Ollama / ArXiv data.",
            f"Vendor: {specs.get('vendor') or 'unknown'}.",
            f"Parameters: {specs.get('parameters')}.",
            f"Context window: {specs.get('context_window')}.",
        ]
        if resources.get("notes"):
            analysis_parts.append("Hosting notes: " + "; ".join(resources["notes"]))
        return {
            "summary": f"Automated profile for {model_name}",
            "analysis": " ".join(str(p) for p in analysis_parts if p),
            "recommendations": [
                "Validate benchmark claims against primary sources before production use.",
                "Prefer quantized local deployment via Ollama when GPU memory is constrained."
                if (resources.get("requirement") or {}).get("hostingOption") == "ollama"
                or (resources.get("requirement") or {}).get("hosting_option") == "ollama"
                else "Size GPU memory to the optimal tier before production traffic.",
            ],
            "flaws": list(capabilities.get("weaknesses") or []),
            "capabilities": {
                "strengths": capabilities.get("strengths") or [],
                "idealUseCases": capabilities.get("ideal_use_cases")
                or capabilities.get("idealUseCases")
                or [],
                "poorUseCases": capabilities.get("poor_use_cases")
                or capabilities.get("poorUseCases")
                or [],
            },
            "competitors": competitors,
        }
