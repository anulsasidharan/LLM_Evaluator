"""Data aggregation: fetch, normalize, and enrich model metadata from sources."""

from __future__ import annotations

from typing import Any

import structlog

from app.config import Settings, get_settings
from app.integrations.arxiv import ArxivSource
from app.integrations.huggingface import HuggingFaceSource
from app.integrations.ollama import OllamaSource

logger = structlog.get_logger(__name__)


class DataService:
    """Coordinates HuggingFace, Ollama, and ArXiv integrations."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._hf = HuggingFaceSource()
        self._ollama = OllamaSource()
        self._arxiv = ArxivSource()

    async def fetch_model_card(self, model_name: str) -> dict[str, Any] | None:
        """Return a normalized HuggingFace model card, or None on failure."""
        logger.info("fetch_model_card", model_name=model_name)
        try:
            raw = await self._hf.fetch(model_name)
            return self._hf.normalize(self._hf.parse(raw))
        except Exception as exc:  # noqa: BLE001
            logger.warning("fetch_model_card_failed", model_name=model_name, error=str(exc))
            return None

    async def fetch_benchmarks(self, model_name: str) -> list[dict[str, Any]]:
        """Return normalized 0–100 benchmark scores for a model."""
        card = await self.fetch_model_card(model_name)
        if not card:
            return []
        benchmarks = card.get("benchmarks") or {}
        return [
            {
                "benchmark_name": name,
                "score": score,
                "source": card.get("source", "huggingface"),
                "source_url": card.get("source_url"),
            }
            for name, score in benchmarks.items()
        ]

    async def fetch_ollama(self, model_name: str) -> dict[str, Any] | None:
        """Return Ollama hosting metadata when available."""
        try:
            raw = await self._ollama.fetch(model_name)
            return self._ollama.normalize(self._ollama.parse(raw))
        except Exception as exc:  # noqa: BLE001
            logger.warning("fetch_ollama_failed", model_name=model_name, error=str(exc))
            return None

    async def fetch_papers(
        self,
        model_name: str,
        topic: str = "architecture",
    ) -> list[dict[str, Any]]:
        """Return ArXiv papers related to the model."""
        query = f"{model_name} {topic}".strip()
        try:
            raw = await self._arxiv.fetch(query)
            normalized = self._arxiv.normalize(self._arxiv.parse(raw))
            papers = normalized.get("papers") or []
            return papers if isinstance(papers, list) else []
        except Exception as exc:  # noqa: BLE001
            logger.warning("fetch_papers_failed", model_name=model_name, error=str(exc))
            return []

    async def search_models(self, query: str, *, limit: int = 10) -> list[dict[str, Any]]:
        """Search HuggingFace for models matching ``query``."""
        try:
            results = await self._hf.search(query, limit=limit)
            hits: list[dict[str, Any]] = []
            for item in results:
                model_id = str(item.get("id") or "")
                hits.append(
                    {
                        "id": model_id,
                        "name": model_id,
                        "vendor": model_id.split("/")[0] if "/" in model_id else "unknown",
                        "parameters": None,
                        "release_date": item.get("createdAt"),
                        "tags": list(item.get("tags") or [])[:12],
                        "downloads": item.get("downloads"),
                    }
                )
            return hits
        except Exception as exc:  # noqa: BLE001
            logger.warning("search_models_failed", query=query, error=str(exc))
            return []

    async def find_competitors(self, model_name: str, category: str = "general") -> list[str]:
        """Identify comparable models via Hub search."""
        seed = model_name.split("/")[-1]
        # Broaden search terms by category
        query = seed
        if category and category != "general":
            query = f"{category} {seed}"
        results = await self.search_models(query, limit=12)
        competitors: list[str] = []
        for hit in results:
            name = hit.get("name")
            if not name:
                continue
            if name.lower() == model_name.lower():
                continue
            if name not in competitors:
                competitors.append(str(name))
            if len(competitors) >= 5:
                break
        return competitors
