"""HuggingFace Hub integration."""

from __future__ import annotations

import re
from typing import Any

import structlog

from app.integrations.base import DataSourceInterface, register_source
from app.integrations.http_client import HttpClient

logger = structlog.get_logger(__name__)

HUGGINGFACE_API_BASE = "https://huggingface.co/api"
HUGGINGFACE_WEB_BASE = "https://huggingface.co"

# Canonical benchmark aliases → standard names
BENCHMARK_ALIASES: dict[str, str] = {
    "mmlu": "MMLU",
    "massive multitask language understanding": "MMLU",
    "hellaswag": "HellaSwag",
    "arc": "ARC",
    "arc-challenge": "ARC",
    "arc challenge": "ARC",
    "truthfulqa": "TruthfulQA",
    "gsm8k": "GSM8K",
    "humaneval": "HumanEval",
    "mbpp": "MBPP",
    "winogrande": "WinoGrande",
    "bbh": "BBH",
    "gpqa": "GPQA",
}


def canonicalize_benchmark(name: str) -> str:
    """Normalize a benchmark label to a canonical form."""
    key = name.strip().lower()
    return BENCHMARK_ALIASES.get(key, name.strip())


def parse_parameter_count(value: Any) -> int | None:
    """Parse parameter counts from ints, floats, or strings like '70B' / '8b'."""
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    text = str(value).strip().lower().replace(",", "")
    match = re.match(r"^([\d.]+)\s*([kmb])?$", text)
    if not match:
        digits = re.findall(r"\d+", text)
        return int(digits[0]) if digits else None
    number = float(match.group(1))
    suffix = match.group(2)
    multipliers = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000}
    if suffix:
        return int(number * multipliers[suffix])
    return int(number)


@register_source
class HuggingFaceSource(DataSourceInterface):
    """Fetches model cards and configs from the HuggingFace Hub API."""

    name = "huggingface"

    def __init__(self, client: HttpClient | None = None) -> None:
        self._client = client or HttpClient()

    async def fetch(self, query: str) -> dict[str, Any]:
        """Resolve a model id (exact or search) and return Hub payload + config."""
        model_id = await self._resolve_model_id(query)
        logger.info("huggingface_fetch", query=query, model_id=model_id)
        model = await self._client.get_json(f"{HUGGINGFACE_API_BASE}/models/{model_id}")
        if not isinstance(model, dict):
            raise ValueError(f"Unexpected HF model payload for {model_id}")

        config: dict[str, Any] = {}
        try:
            config_resp = await self._client.get_json(
                f"https://huggingface.co/{model_id}/raw/main/config.json"
            )
            if isinstance(config_resp, dict):
                config = config_resp
        except Exception as exc:  # noqa: BLE001 — config is optional
            logger.info("huggingface_config_unavailable", model_id=model_id, error=str(exc))

        return {"model": model, "config": config, "model_id": model_id}

    async def search(self, query: str, *, limit: int = 8) -> list[dict[str, Any]]:
        """Search Hub models by name."""
        data = await self._client.get_json(
            f"{HUGGINGFACE_API_BASE}/models",
            params={
                "search": query,
                "limit": limit,
                "sort": "downloads",
                "direction": -1,
            },
        )
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        return []

    async def _resolve_model_id(self, query: str) -> str:
        cleaned = query.strip().replace(" ", "-")
        # Try exact id first
        try:
            data = await self._client.get_json(f"{HUGGINGFACE_API_BASE}/models/{cleaned}")
            if isinstance(data, dict) and data.get("id"):
                return str(data["id"])
        except Exception:  # noqa: BLE001
            pass

        # Common org prefixes
        for candidate in (
            cleaned,
            f"meta-llama/{cleaned}",
            f"mistralai/{cleaned}",
            f"google/{cleaned}",
            f"microsoft/{cleaned}",
            f"Qwen/{cleaned}",
            f"openai/{cleaned}",
            f"HuggingFaceH4/{cleaned}",
        ):
            try:
                data = await self._client.get_json(f"{HUGGINGFACE_API_BASE}/models/{candidate}")
                if isinstance(data, dict) and data.get("id"):
                    return str(data["id"])
            except Exception:  # noqa: BLE001
                continue

        results = await self.search(query, limit=5)
        if not results:
            raise LookupError(f"No HuggingFace model found for '{query}'")
        return str(results[0].get("id") or results[0].get("modelId"))

    def parse(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Pull id, tags, card data, and config from a Hub payload."""
        model = raw.get("model") if isinstance(raw.get("model"), dict) else raw
        config = raw.get("config") if isinstance(raw.get("config"), dict) else {}
        card = model.get("cardData") or {}
        siblings = model.get("siblings") or []
        return {
            "id": model.get("id") or model.get("modelId") or raw.get("model_id"),
            "pipeline_tag": model.get("pipeline_tag"),
            "tags": list(model.get("tags") or []),
            "downloads": model.get("downloads"),
            "likes": model.get("likes"),
            "created_at": model.get("createdAt") or model.get("created_at"),
            "last_modified": model.get("lastModified") or model.get("last_modified"),
            "card_data": card if isinstance(card, dict) else {},
            "config": config,
            "siblings": siblings if isinstance(siblings, list) else [],
            "private": model.get("private", False),
            "author": (str(model.get("id", "")).split("/")[0] if model.get("id") else None),
        }

    def normalize(self, parsed: dict[str, Any]) -> dict[str, Any]:
        """Map Hub fields onto the ModelProfile shape plus benchmarks."""
        card = parsed.get("card_data") or {}
        config = parsed.get("config") or {}
        tags = list(parsed.get("tags") or [])
        if parsed.get("pipeline_tag") and parsed["pipeline_tag"] not in tags:
            tags.insert(0, parsed["pipeline_tag"])

        parameters = (
            parse_parameter_count(card.get("params"))
            or parse_parameter_count(card.get("model-index") and None)
            or parse_parameter_count(config.get("num_parameters"))
            or self._parameters_from_tags(tags)
            or self._parameters_from_safetensors(parsed)
        )

        context_window = (
            config.get("max_position_embeddings")
            or config.get("n_positions")
            or config.get("max_sequence_length")
            or card.get("context_length")
        )
        if isinstance(context_window, str):
            context_window = parse_parameter_count(context_window)

        benchmarks = self._extract_benchmarks(card)
        description = ""
        if isinstance(card.get("description"), str):
            description = card["description"]

        model_id = parsed.get("id")
        return self.with_provenance(
            {
                "name": model_id,
                "vendor": parsed.get("author") or "unknown",
                "parameters": parameters,
                "release_date": parsed.get("created_at"),
                "description": description,
                "official_url": f"{HUGGINGFACE_WEB_BASE}/{model_id}" if model_id else None,
                "tags": tags,
                "specs": {
                    "context_window": context_window,
                    "architecture": config.get("model_type") or config.get("architectures"),
                    "precision": self._infer_precision(tags),
                    "training_data_cutoff": card.get("training_data_cutoff"),
                },
                "benchmarks": benchmarks,
                "downloads": parsed.get("downloads"),
                "likes": parsed.get("likes"),
            },
            source_url=f"{HUGGINGFACE_WEB_BASE}/{model_id}" if model_id else HUGGINGFACE_API_BASE,
        )

    def _parameters_from_tags(self, tags: list[str]) -> int | None:
        for tag in tags:
            match = re.search(r"(\d+(?:\.\d+)?)\s*[bB]", tag)
            if match:
                return parse_parameter_count(f"{match.group(1)}B")
        return None

    def _parameters_from_safetensors(self, parsed: dict[str, Any]) -> int | None:
        card = parsed.get("card_data") or {}
        safetensors = card.get("safetensors") if isinstance(card, dict) else None
        if isinstance(safetensors, dict):
            total = safetensors.get("total")
            if isinstance(total, (int, float)):
                return int(total)
        return None

    def _infer_precision(self, tags: list[str]) -> list[str]:
        found: list[str] = []
        joined = " ".join(tags).lower()
        for label in ("fp32", "fp16", "bf16", "int8", "int4", "gptq", "awq"):
            if label in joined:
                if label.startswith(("fp", "bf", "int")):
                    found.append(label.upper())
                else:
                    found.append(label.upper())
        return found or ["FP16"]

    def _extract_benchmarks(self, card: dict[str, Any]) -> dict[str, float | None]:
        """Extract and normalize benchmark scores from model-index / card fields."""
        results: dict[str, float | None] = {}
        model_index = card.get("model-index")
        if isinstance(model_index, list):
            for entry in model_index:
                if not isinstance(entry, dict):
                    continue
                for result in entry.get("results") or []:
                    if not isinstance(result, dict):
                        continue
                    dataset = result.get("dataset") or {}
                    name = dataset.get("name") or result.get("task", {}).get("name") or "unknown"
                    metrics = result.get("metrics") or []
                    for metric in metrics:
                        if not isinstance(metric, dict):
                            continue
                        value = metric.get("value")
                        if isinstance(value, (int, float)):
                            results[canonicalize_benchmark(str(name))] = self._to_100(float(value))
        # Flat evaluation fields sometimes present
        for key, value in card.items():
            if isinstance(value, (int, float)) and key.lower() in BENCHMARK_ALIASES:
                results[canonicalize_benchmark(key)] = self._to_100(float(value))
        return results

    @staticmethod
    def _to_100(score: float) -> float:
        """Normalize scores that look like 0–1 ratios onto 0–100."""
        if 0.0 <= score <= 1.0:
            return round(score * 100.0, 2)
        return round(score, 2)
