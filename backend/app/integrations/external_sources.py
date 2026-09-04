"""Vendor / vLLM documentation scrapers (scaffold)."""

from typing import Any

import structlog

from app.integrations.base import DataSourceInterface, register_source

logger = structlog.get_logger(__name__)


@register_source
class VendorSource(DataSourceInterface):
    """Scrapes official vendor pages for claimed benchmarks and specs."""

    name = "vendor"

    async def fetch(self, query: str) -> dict[str, Any]:
        """Scrape a vendor page. Not implemented until Playwright is wired."""
        logger.info("vendor_fetch", query=query)
        raise NotImplementedError("Vendor page scraping is not implemented yet.")

    def parse(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Pass through scraped sections until parsers exist per vendor."""
        return {"raw_text": raw.get("text", ""), "url": raw.get("url")}

    def normalize(self, parsed: dict[str, Any]) -> dict[str, Any]:
        """Attach provenance; scores stay null until extractors exist."""
        return self.with_provenance(
            {"official_url": parsed.get("url"), "benchmarks": {}},
            source_url=parsed.get("url"),
        )


@register_source
class VllmSource(DataSourceInterface):
    """Scrapes vLLM docs for inference optimization guidance."""

    name = "vllm"

    async def fetch(self, query: str) -> dict[str, Any]:
        """Fetch vLLM docs. Not implemented until HTTP client is wired."""
        logger.info("vllm_fetch", query=query)
        raise NotImplementedError("vLLM docs client is not implemented yet.")

    def parse(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Extract relevant doc sections."""
        return {"sections": raw.get("sections", [])}

    def normalize(self, parsed: dict[str, Any]) -> dict[str, Any]:
        """Map docs onto hosting notes."""
        return self.with_provenance(
            {"hosting_option": "vllm", "notes": parsed.get("sections", [])}
        )
