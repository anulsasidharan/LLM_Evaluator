"""API route tests for analyze, results, search, and comparisons."""

from uuid import uuid4

import pytest
from httpx import AsyncClient


async def test_analyze_returns_202_with_job_id(client: AsyncClient) -> None:
    """POST /models/analyze queues a job and returns a poll URL."""
    response = await client.post(
        "/api/v1/models/analyze",
        json={"modelName": "claude-3-opus", "depth": "quick"},
    )
    assert response.status_code == 202
    data = response.json()["data"]
    assert data["status"] == "queued"
    assert data["jobId"]
    assert data["resultsUrl"].startswith("/api/v1/results/")


async def test_analyze_rejects_empty_model_name(client: AsyncClient) -> None:
    """POST /models/analyze returns 422 when modelName is empty."""
    response = await client.post("/api/v1/models/analyze", json={"modelName": ""})
    assert response.status_code == 422
    body = response.json()
    assert body["data"] is None
    assert body["error"]["code"] == "validation_error"


async def test_get_results_not_found(client: AsyncClient) -> None:
    """GET /results/{id} returns 404 for an unknown job."""
    response = await client.get(f"/api/v1/results/{uuid4()}")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "job_not_found"


async def test_analyze_then_poll_completes(client: AsyncClient) -> None:
    """The in-process scaffold completes analysis before the first poll."""
    created = await client.post(
        "/api/v1/models/analyze",
        json={"modelName": "gpt-4-turbo", "depth": "standard"},
    )
    job_id = created.json()["data"]["jobId"]
    polled = await client.get(f"/api/v1/results/{job_id}")
    assert polled.status_code == 200
    payload = polled.json()["data"]
    assert payload["status"] == "completed"
    assert payload["report"]["model"]["name"] == "gpt-4-turbo"


async def test_search_returns_results(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """GET /models/search returns Hub hits from the data service."""
    from app.api import routes as routes_module

    class _FakeData:
        async def search_models(self, query: str, *, limit: int = 10):
            return [
                {
                    "name": "meta-llama/Llama-3.1-8B-Instruct",
                    "vendor": "meta-llama",
                    "parameters": None,
                    "release_date": None,
                    "tags": ["text-generation"],
                }
            ]

    monkeypatch.setattr(routes_module, "DataService", _FakeData)
    response = await client.get("/api/v1/models/search", params={"q": "llama"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 1
    assert data["results"][0]["name"] == "meta-llama/Llama-3.1-8B-Instruct"


async def test_create_comparison(client: AsyncClient) -> None:
    """POST /comparisons returns 201 with a comparison id."""
    response = await client.post(
        "/api/v1/comparisons",
        json={"modelIds": [str(uuid4()), str(uuid4())], "focusAreas": ["capabilities"]},
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["comparisonId"]
    assert "comparison" in data
