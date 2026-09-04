"""Shared async HTTP client with timeouts and exponential backoff."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
import structlog

from app.config import get_settings

logger = structlog.get_logger(__name__)


class HttpClient:
    """Thin wrapper around httpx with retries for transient failures."""

    def __init__(self) -> None:
        settings = get_settings()
        self._timeout = settings.http_timeout_seconds
        self._max_retries = settings.http_max_retries
        self._headers: dict[str, str] = {
            "User-Agent": "LLM-Evaluator/0.1 (+https://github.com/local/llm-evaluator)",
            "Accept": "application/json, application/atom+xml, text/html;q=0.9,*/*;q=0.8",
        }
        if settings.huggingface_api_token:
            self._headers["Authorization"] = f"Bearer {settings.huggingface_api_token}"

    async def get_json(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any] | list[Any]:
        """GET JSON with retries. Raises httpx.HTTPError on final failure."""
        response = await self._request("GET", url, params=params, headers=headers)
        return response.json()

    async def get_text(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> str:
        """GET text/HTML/XML with retries."""
        response = await self._request("GET", url, params=params, headers=headers)
        return response.text

    async def get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """GET raw response with retries."""
        return await self._request("GET", url, params=params, headers=headers)

    async def _request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        merged = {**self._headers, **(headers or {})}
        delay = 2.0
        last_error: Exception | None = None

        async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
            for attempt in range(1, self._max_retries + 1):
                try:
                    response = await client.request(method, url, params=params, headers=merged)
                    if response.status_code in {429, 500, 502, 503, 504}:
                        raise httpx.HTTPStatusError(
                            f"Transient status {response.status_code}",
                            request=response.request,
                            response=response,
                        )
                    response.raise_for_status()
                    return response
                except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError) as exc:
                    last_error = exc
                    logger.warning(
                        "http_retry",
                        url=url,
                        attempt=attempt,
                        error=str(exc),
                    )
                    if attempt >= self._max_retries:
                        break
                    await asyncio.sleep(min(delay, 60.0))
                    delay *= 2

        assert last_error is not None
        raise last_error
