"""ArXiv API integration."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import quote_plus

import structlog

from app.integrations.base import DataSourceInterface, register_source
from app.integrations.http_client import HttpClient

logger = structlog.get_logger(__name__)

ARXIV_API_BASE = "https://export.arxiv.org/api/query"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


@register_source
class ArxivSource(DataSourceInterface):
    """Searches ArXiv for papers related to a model."""

    name = "arxiv"

    def __init__(self, client: HttpClient | None = None) -> None:
        self._client = client or HttpClient()

    async def fetch(self, query: str) -> dict[str, Any]:
        """Query the ArXiv Atom API for papers matching ``query``."""
        search = f'all:"{query}" OR ti:"{query}"'
        params = (
            f"search_query={quote_plus(search)}"
            "&start=0&max_results=8&sortBy=relevance&sortOrder=descending"
        )
        url = f"{ARXIV_API_BASE}?{params}"
        logger.info("arxiv_fetch", query=query)
        text = await self._client.get_text(
            url,
            headers={"Accept": "application/atom+xml"},
        )
        return {"xml": text, "query": query}

    def parse(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Extract paper entries from an Atom feed."""
        xml_text = raw.get("xml") or ""
        entries: list[dict[str, Any]] = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return {"entries": [], "query": raw.get("query")}

        for entry in root.findall("atom:entry", ATOM_NS):
            title = (entry.findtext("atom:title", default="", namespaces=ATOM_NS) or "").strip()
            summary = (
                entry.findtext("atom:summary", default="", namespaces=ATOM_NS) or ""
            ).strip()
            entry_id = (entry.findtext("atom:id", default="", namespaces=ATOM_NS) or "").strip()
            published = (
                entry.findtext("atom:published", default="", namespaces=ATOM_NS) or ""
            ).strip()
            authors = [
                (author.findtext("atom:name", default="", namespaces=ATOM_NS) or "").strip()
                for author in entry.findall("atom:author", ATOM_NS)
            ]
            entries.append(
                {
                    "title": " ".join(title.split()),
                    "summary": " ".join(summary.split())[:500],
                    "id": entry_id,
                    "url": entry_id,
                    "published": published,
                    "authors": [a for a in authors if a],
                }
            )
        return {"entries": entries, "query": raw.get("query")}

    def normalize(self, parsed: dict[str, Any]) -> dict[str, Any]:
        """Return papers with canonical title/id/url fields."""
        papers = []
        for entry in parsed.get("entries", []):
            papers.append(
                {
                    "title": entry.get("title"),
                    "arxiv_id": entry.get("id"),
                    "url": entry.get("url") or entry.get("id"),
                    "published": entry.get("published"),
                    "authors": entry.get("authors", []),
                    "summary": entry.get("summary"),
                }
            )
        return self.with_provenance({"papers": papers}, source_url=ARXIV_API_BASE)
