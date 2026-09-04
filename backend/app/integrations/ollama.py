"""Ollama registry / library integration."""

from __future__ import annotations

import re
from typing import Any

import structlog

from app.integrations.base import DataSourceInterface, register_source
from app.integrations.http_client import HttpClient
from app.integrations.huggingface import parse_parameter_count

logger = structlog.get_logger(__name__)

OLLAMA_LIBRARY_BASE = "https://ollama.com/library"
OLLAMA_TAGS_HINT = "https://ollama.com"


@register_source
class OllamaSource(DataSourceInterface):
    """Looks up local-hosting compatibility in the Ollama library."""

    name = "ollama"

    def __init__(self, client: HttpClient | None = None) -> None:
        self._client = client or HttpClient()

    async def fetch(self, query: str) -> dict[str, Any]:
        """Fetch Ollama library page for a model slug."""
        slug = self._to_slug(query)
        url = f"{OLLAMA_LIBRARY_BASE}/{slug}"
        logger.info("ollama_fetch", query=query, slug=slug, url=url)
        try:
            response = await self._client.get(url, headers={"Accept": "text/html"})
            return {
                "slug": slug,
                "url": str(response.url),
                "status_code": response.status_code,
                "html": response.text,
                "available": response.status_code == 200,
            }
        except Exception as exc:  # noqa: BLE001
            logger.info("ollama_unavailable", slug=slug, error=str(exc))
            # Fallback: try base name without org/version suffixes
            alt = slug.split("/")[-1].split(":")[0]
            if alt != slug:
                try:
                    alt_url = f"{OLLAMA_LIBRARY_BASE}/{alt}"
                    response = await self._client.get(alt_url, headers={"Accept": "text/html"})
                    return {
                        "slug": alt,
                        "url": str(response.url),
                        "status_code": response.status_code,
                        "html": response.text,
                        "available": response.status_code == 200,
                    }
                except Exception as alt_exc:  # noqa: BLE001
                    logger.info("ollama_alt_unavailable", slug=alt, error=str(alt_exc))
            return {
                "slug": slug,
                "url": url,
                "status_code": None,
                "html": "",
                "available": False,
                "error": str(exc),
            }

    def parse(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Extract name, tags, and size hints from library HTML."""
        html = raw.get("html") or ""
        tags = sorted(set(re.findall(r"/library/[\w.-]+:([\w.-]+)", html)))
        sizes = re.findall(r"(\d+(?:\.\d+)?\s*[KMGT]B)", html, flags=re.IGNORECASE)
        param_matches = re.findall(r"(\d+(?:\.\d+)?)\s*[Bb]\s*param", html)
        parameters = None
        if param_matches:
            parameters = parse_parameter_count(f"{param_matches[0]}B")
        description_match = re.search(
            r'<meta\s+name="description"\s+content="([^"]+)"',
            html,
            flags=re.IGNORECASE,
        )
        return {
            "name": raw.get("slug"),
            "tags": tags[:20],
            "sizes": sizes[:10],
            "parameters": parameters,
            "available": bool(raw.get("available")),
            "url": raw.get("url"),
            "description": description_match.group(1) if description_match else "",
        }

    def normalize(self, parsed: dict[str, Any]) -> dict[str, Any]:
        """Map Ollama fields onto hosting-oriented model metadata."""
        return self.with_provenance(
            {
                "name": parsed.get("name"),
                "hosting_option": "ollama",
                "available_on_ollama": bool(parsed.get("available")),
                "tags": parsed.get("tags", []),
                "sizes": parsed.get("sizes", []),
                "parameters": parsed.get("parameters"),
                "description": parsed.get("description") or "",
                "official_url": parsed.get("url"),
            },
            source_url=parsed.get("url") or OLLAMA_LIBRARY_BASE,
        )

    @staticmethod
    def _to_slug(query: str) -> str:
        text = query.strip().lower()
        text = text.replace(" ", "-")
        # Strip org prefixes commonly used on HF
        if "/" in text:
            text = text.split("/")[-1]
        text = re.sub(r"^meta-llama-", "", text)
        text = text.removeprefix("llama-")
        # Map common HF names to Ollama library names
        replacements = {
            "meta-llama/llama-3.1-8b-instruct": "llama3.1",
            "llama-3.1-8b-instruct": "llama3.1",
            "llama-3.1-8b": "llama3.1",
            "llama-3-8b-instruct": "llama3",
            "llama-3-8b": "llama3",
            "mistral-7b-instruct-v0.2": "mistral",
            "mistral-7b-instruct": "mistral",
            "mixtral-8x7b-instruct": "mixtral",
            "gemma-2-9b-it": "gemma2",
            "gemma-7b-it": "gemma",
            "qwen2.5-7b-instruct": "qwen2.5",
            "phi-3-mini-4k-instruct": "phi3",
        }
        for key, value in replacements.items():
            if text == key or text.endswith(key):
                return value
        # Compress llama3.1 style
        text = text.replace("llama-3.1", "llama3.1").replace("llama-3", "llama3")
        text = re.sub(r"-instruct.*$", "", text)
        text = re.sub(r"-\d+b.*$", "", text)
        return text or query.strip().lower()
