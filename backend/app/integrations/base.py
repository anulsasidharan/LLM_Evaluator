"""Shared contract for every external data source."""

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any


class DataSourceInterface(ABC):
    """Fetch → parse → normalize pipeline for one upstream provider."""

    name: str

    @abstractmethod
    async def fetch(self, query: str) -> dict[str, Any]:
        """Retrieve the raw payload for ``query`` from the upstream API."""

    @abstractmethod
    def parse(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Extract the fields we care about from a raw response."""

    @abstractmethod
    def normalize(self, parsed: dict[str, Any]) -> dict[str, Any]:
        """Convert parsed data into canonical field names and 0–100 scores."""

    def with_provenance(
        self,
        record: dict[str, Any],
        source_url: str | None = None,
    ) -> dict[str, Any]:
        """Stamp source metadata required by the data-pipeline rules."""
        return {
            **record,
            "source": self.name,
            "source_url": source_url,
            "scraped_at": datetime.now(UTC).isoformat(),
        }


_REGISTRY: dict[str, type[DataSourceInterface]] = {}


def register_source(cls: type[DataSourceInterface]) -> type[DataSourceInterface]:
    """Class decorator that registers a data source by its ``name``."""
    _REGISTRY[cls.name] = cls
    return cls


def get_source(name: str) -> DataSourceInterface:
    """Instantiate a registered source by name.

    Raises:
        KeyError: If no source is registered under ``name``.
    """
    if name not in _REGISTRY:
        available = ", ".join(sorted(_REGISTRY)) or "(none)"
        raise KeyError(f"Unknown data source '{name}'. Registered: {available}")
    return _REGISTRY[name]()


def list_sources() -> list[str]:
    """Return registered source names."""
    return sorted(_REGISTRY)
