"""Tool executor tests with mocked data service."""

from __future__ import annotations

import pytest

from app.services.tool_executor import ToolExecutor


class _FakeData:
    async def fetch_benchmarks(self, model_name: str):
        return [
            {
                "benchmark_name": "MMLU",
                "score": 68.5,
                "source": "huggingface",
                "source_url": "https://huggingface.co/example",
            }
        ]

    async def fetch_model_card(self, model_name: str):
        return {
            "name": model_name,
            "vendor": "meta-llama",
            "parameters": 8_000_000_000,
            "description": "test",
            "official_url": "https://huggingface.co/example",
            "tags": ["text-generation", "instruct"],
            "specs": {"context_window": 8192, "architecture": "llama", "precision": ["FP16"]},
            "benchmarks": {"MMLU": 68.5},
            "source": "huggingface",
            "source_url": "https://huggingface.co/example",
        }

    async def fetch_ollama(self, model_name: str):
        return {"available_on_ollama": True, "name": "llama3.1", "parameters": 8_000_000_000}

    async def find_competitors(self, model_name: str, category: str = "general"):
        return ["mistralai/Mistral-7B-Instruct-v0.2"]

    async def fetch_papers(self, model_name: str, topic: str = "architecture"):
        return [{"title": "Example", "url": "https://arxiv.org/abs/0000.00000"}]


@pytest.mark.asyncio
async def test_search_benchmarks_tool() -> None:
    executor = ToolExecutor(data_service=_FakeData())  # type: ignore[arg-type]
    result = await executor.execute("search_benchmarks", {"model_name": "llama3"})
    assert result["benchmarks"][0]["benchmark_name"] == "MMLU"


@pytest.mark.asyncio
async def test_gather_for_model_returns_core_sections() -> None:
    executor = ToolExecutor(data_service=_FakeData())  # type: ignore[arg-type]
    gathered = await executor.gather_for_model("meta-llama/Llama-3.1-8B-Instruct")
    assert "specs" in gathered
    assert "resources" in gathered
    assert gathered["competitors"]["competitors"]
