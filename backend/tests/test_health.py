"""Health and root endpoint tests."""

from httpx import AsyncClient


async def test_health_returns_ok(client: AsyncClient) -> None:
    """GET /api/v1/health returns the standard envelope with status ok."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["error"] is None
    assert body["data"]["status"] == "ok"
    assert "version" in body["data"]


async def test_root_returns_ok(client: AsyncClient) -> None:
    """GET / returns a liveness payload."""
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "ok"
