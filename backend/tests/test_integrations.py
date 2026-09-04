"""Data source registry tests."""

from app.integrations.arxiv import ArxivSource
from app.integrations.base import get_source, list_sources
from app.integrations.huggingface import HuggingFaceSource
from app.integrations.ollama import OllamaSource


def test_registered_sources_include_primary_providers() -> None:
    """HuggingFace, ArXiv, and Ollama register themselves on import."""
    names = set(list_sources())
    assert {"huggingface", "arxiv", "ollama", "vendor", "vllm"}.issubset(names)


def test_get_source_returns_huggingface() -> None:
    """get_source instantiates the HuggingFace adapter."""
    source = get_source("huggingface")
    assert isinstance(source, HuggingFaceSource)
    assert source.name == "huggingface"


def test_unknown_source_raises_key_error() -> None:
    """Looking up an unregistered source raises a helpful KeyError."""
    try:
        get_source("not-a-real-source")
        raise AssertionError("Expected KeyError")
    except KeyError as exc:
        assert "not-a-real-source" in str(exc)


def test_huggingface_normalize_adds_provenance() -> None:
    """Normalized records include source and scraped_at."""
    source = HuggingFaceSource()
    parsed = source.parse({"id": "meta-llama/Llama-3-8B", "pipeline_tag": "text-generation"})
    normalized = source.normalize(parsed)
    assert normalized["source"] == "huggingface"
    assert "scraped_at" in normalized
    assert normalized["name"] == "meta-llama/Llama-3-8B"


def test_arxiv_and_ollama_have_stable_names() -> None:
    """Source name attributes match registry keys."""
    assert ArxivSource.name == "arxiv"
    assert OllamaSource.name == "ollama"
