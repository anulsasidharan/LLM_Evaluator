"""Execute LLM tools against data services and calculators."""

from __future__ import annotations

import json
from typing import Any

import structlog

from app.api.tools import (
    AnalyzeCapabilitiesOutput,
    CalculateResourceRequirementsOutput,
    ExtractPerformanceMetricsOutput,
    FetchModelSpecsOutput,
    FetchResearchPapersOutput,
    FindCompetitorsOutput,
    GenerateTradeOffAnalysisOutput,
    SearchBenchmarksOutput,
)
from app.models.schemas import DeploymentType
from app.services.data_service import DataService
from app.services.resource_calculator import calculate_resource_requirements, estimate_gpu_memory_gb

logger = structlog.get_logger(__name__)


class ToolExecutor:
    """Dispatches tool calls by name. All tools are idempotent."""

    def __init__(self, data_service: DataService | None = None) -> None:
        self._data = data_service or DataService()
        self._handlers = {
            "search_benchmarks": self._search_benchmarks,
            "fetch_model_specs": self._fetch_model_specs,
            "analyze_capabilities": self._analyze_capabilities,
            "find_competitors": self._find_competitors,
            "calculate_resource_requirements": self._calculate_resources,
            "generate_trade_off_analysis": self._trade_offs,
            "fetch_research_papers": self._fetch_papers,
            "extract_performance_metrics": self._extract_metrics,
        }

    async def execute(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Run a named tool and return a JSON-serializable result dict."""
        handler = self._handlers.get(name)
        if handler is None:
            return {"error": f"Unknown tool '{name}'"}
        logger.info("tool_call", tool=name, arguments=arguments)
        try:
            result = await handler(arguments)
            logger.info("tool_result", tool=name, ok=True)
            return result
        except Exception as exc:  # noqa: BLE001
            logger.error("tool_failed", tool=name, error=str(exc))
            return {"error": str(exc), "tool": name}

    async def gather_for_model(self, model_name: str) -> dict[str, Any]:
        """Run the core analysis tools for a model (deterministic gathering)."""
        specs = await self._fetch_model_specs({"model_name": model_name})
        benchmarks = await self._search_benchmarks({"model_name": model_name})
        capabilities = await self._analyze_capabilities({"model_name": model_name})
        competitors = await self._find_competitors({"model_name": model_name})
        resources = await self._calculate_resources(
            {"model_name": model_name, "deployment_type": "local"}
        )
        papers = await self._fetch_papers({"model_name": model_name, "topic": "architecture"})
        metrics = await self._extract_metrics({"model_name": model_name})
        return {
            "specs": specs,
            "benchmarks": benchmarks,
            "capabilities": capabilities,
            "competitors": competitors,
            "resources": resources,
            "papers": papers,
            "metrics": metrics,
        }

    async def _search_benchmarks(self, args: dict[str, Any]) -> dict[str, Any]:
        model_name = str(args["model_name"])
        rows = await self._data.fetch_benchmarks(model_name)
        notes: list[str] = []
        if not rows:
            notes.append("No benchmark scores found on HuggingFace model card.")
        out = SearchBenchmarksOutput(model_name=model_name, benchmarks=rows, source_notes=notes)
        return out.model_dump(mode="json")

    async def _fetch_model_specs(self, args: dict[str, Any]) -> dict[str, Any]:
        model_name = str(args["model_name"])
        card = await self._data.fetch_model_card(model_name)
        ollama = await self._data.fetch_ollama(model_name)
        if not card:
            out = FetchModelSpecsOutput(model_name=model_name)
            payload = out.model_dump(mode="json")
            payload["ollama"] = ollama
            payload["notes"] = ["Model card unavailable from HuggingFace."]
            return payload

        specs = card.get("specs") or {}
        architecture = specs.get("architecture")
        if isinstance(architecture, list):
            architecture = ", ".join(str(x) for x in architecture)

        parameters = card.get("parameters")
        if parameters is None and ollama:
            parameters = ollama.get("parameters")

        out = FetchModelSpecsOutput(
            model_name=str(card.get("name") or model_name),
            vendor=card.get("vendor"),
            parameters=parameters,
            context_window=specs.get("context_window"),
            architecture=str(architecture) if architecture else None,
            precision=list(specs.get("precision") or []),
            official_url=card.get("official_url"),
        )
        payload = out.model_dump(mode="json")
        payload["description"] = card.get("description") or ""
        payload["tags"] = card.get("tags") or []
        payload["benchmarks"] = card.get("benchmarks") or {}
        payload["ollama"] = ollama
        payload["source"] = card.get("source")
        payload["source_url"] = card.get("source_url")
        return payload

    async def _analyze_capabilities(self, args: dict[str, Any]) -> dict[str, Any]:
        model_name = str(args["model_name"])
        card = await self._data.fetch_model_card(model_name)
        tags = [str(t).lower() for t in (card or {}).get("tags") or []]
        benchmarks = (card or {}).get("benchmarks") or {}

        strengths: list[str] = []
        weaknesses: list[str] = []
        ideal: list[str] = []
        poor: list[str] = []

        if "text-generation" in tags or "conversational" in tags:
            strengths.append("General-purpose text generation / chat")
            ideal.append("Chat assistants and content drafting")
        if any("code" in t for t in tags) or "HumanEval" in benchmarks:
            strengths.append("Code generation")
            ideal.append("Software engineering assistance")
        if any(t in tags for t in ("image-text-to-text", "visual-question-answering")):
            strengths.append("Multimodal (vision) understanding")
            ideal.append("Document and image Q&A")
        if any("instruct" in t or "chat" in t for t in tags):
            strengths.append("Instruction following")
        if not strengths:
            strengths.append("Capabilities inferred from limited metadata only")

        params = (card or {}).get("parameters")
        if params and params < 3_000_000_000:
            weaknesses.append("Smaller parameter count may limit complex reasoning")
            poor.append("Frontier-level research tasks")
        if not benchmarks:
            weaknesses.append("No published benchmark scores found on the model card")
        if "gguf" in tags or "quantized" in " ".join(tags):
            weaknesses.append("Quantized weights may trade accuracy for footprint")

        if not ideal:
            ideal.append("General NLP tasks where this model's size is appropriate")
        if not poor:
            poor.append("Use cases requiring verified benchmark leadership without cited scores")

        out = AnalyzeCapabilitiesOutput(
            model_name=model_name,
            strengths=strengths,
            weaknesses=weaknesses,
            ideal_use_cases=ideal,
            poor_use_cases=poor,
        )
        return out.model_dump(mode="json")

    async def _find_competitors(self, args: dict[str, Any]) -> dict[str, Any]:
        model_name = str(args["model_name"])
        category = str(args.get("category") or "general")
        competitors = await self._data.find_competitors(model_name, category)
        out = FindCompetitorsOutput(model_name=model_name, competitors=competitors)
        return out.model_dump(mode="json")

    async def _calculate_resources(self, args: dict[str, Any]) -> dict[str, Any]:
        model_name = str(args["model_name"])
        deployment = str(args.get("deployment_type") or "local")
        try:
            deployment_type = DeploymentType(deployment)
        except ValueError:
            deployment_type = DeploymentType.LOCAL

        card = await self._data.fetch_model_card(model_name)
        ollama = await self._data.fetch_ollama(model_name)
        parameters = (card or {}).get("parameters") or (ollama or {}).get("parameters")
        precision_list = ((card or {}).get("specs") or {}).get("precision") or ["FP16"]
        precision = str(precision_list[0]).lower() if precision_list else "fp16"

        requirement = calculate_resource_requirements(
            parameters=parameters,
            deployment_type=deployment_type,
            ollama_available=bool((ollama or {}).get("available_on_ollama")),
            precision=precision,
        )
        out = CalculateResourceRequirementsOutput(
            model_name=model_name,
            deployment_type=deployment_type,
            gpu_memory_gb_minimum=estimate_gpu_memory_gb(parameters, "int8"),
            gpu_memory_gb_optimal=estimate_gpu_memory_gb(parameters, precision),
            notes=[
                (
                    f"Estimated from ~{parameters} parameters"
                    if parameters
                    else "Parameter count unknown; using defaults"
                ),
                (
                    "Ollama library: available"
                    if (ollama or {}).get("available_on_ollama")
                    else "Ollama library: not found"
                ),
            ],
        )
        payload = out.model_dump(mode="json")
        payload["requirement"] = requirement.model_dump(mode="json")
        return payload

    async def _trade_offs(self, args: dict[str, Any]) -> dict[str, Any]:
        model1 = str(args["model1"])
        model2 = str(args["model2"])
        specs1 = await self._fetch_model_specs({"model_name": model1})
        specs2 = await self._fetch_model_specs({"model_name": model2})
        trade_offs: list[str] = []
        p1, p2 = specs1.get("parameters"), specs2.get("parameters")
        if p1 and p2:
            if p1 > p2:
                trade_offs.append(
                    f"{model1} is larger ({p1} vs {p2} params) — stronger but heavier"
                )
            elif p2 > p1:
                trade_offs.append(
                    f"{model2} is larger ({p2} vs {p1} params) — stronger but heavier"
                )
            else:
                trade_offs.append(
                    "Similar parameter counts; compare benchmarks and context window"
                )
        c1, c2 = specs1.get("context_window"), specs2.get("context_window")
        if c1 and c2 and c1 != c2:
            trade_offs.append(f"Context window: {model1}={c1}, {model2}={c2}")
        if not trade_offs:
            trade_offs.append(
                "Insufficient published specs for a detailed trade-off; compare Hub cards"
            )
        out = GenerateTradeOffAnalysisOutput(
            model1=model1,
            model2=model2,
            trade_offs=trade_offs,
            recommendation=(
                f"Prefer {model1} if you already depend on its ecosystem; "
                "otherwise validate with benchmarks."
            ),
        )
        return out.model_dump(mode="json")

    async def _fetch_papers(self, args: dict[str, Any]) -> dict[str, Any]:
        model_name = str(args["model_name"])
        topic = str(args.get("topic") or "architecture")
        papers = await self._data.fetch_papers(model_name, topic)
        out = FetchResearchPapersOutput(model_name=model_name, papers=papers)
        return out.model_dump(mode="json")

    async def _extract_metrics(self, args: dict[str, Any]) -> dict[str, Any]:
        model_name = str(args["model_name"])
        rows = await self._data.fetch_benchmarks(model_name)
        metrics = {row["benchmark_name"]: row.get("score") for row in rows}
        out = ExtractPerformanceMetricsOutput(model_name=model_name, metrics=metrics)
        return out.model_dump(mode="json")


def dumps_tool_result(result: dict[str, Any]) -> str:
    """Serialize a tool result for LLM messages."""
    return json.dumps(result, default=str)
