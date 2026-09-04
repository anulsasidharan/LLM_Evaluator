"""Shared pytest fixtures."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

# Force in-memory job store before app imports settings
os.environ["JOB_STORE"] = "memory"
os.environ.setdefault("DEBUG", "true")

from app.api.deps import reset_singletons  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.models.schemas import AnalysisReport, ModelProfile, ModelSpecs  # noqa: E402
from app.services import analysis_service as analysis_module  # noqa: E402

get_settings.cache_clear()
reset_singletons()


@pytest.fixture(autouse=True)
def _reset_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure each test uses the in-memory job store."""
    monkeypatch.setenv("JOB_STORE", "memory")
    get_settings.cache_clear()
    reset_singletons()


@pytest.fixture(autouse=True)
def _stub_analysis(monkeypatch: pytest.MonkeyPatch) -> None:
    """Avoid live HF/OpenAI calls in API route tests."""

    async def _fake_build_report(self, request):  # type: ignore[no-untyped-def]
        now = datetime.now(UTC)
        return AnalysisReport(
            model=ModelProfile(
                id=uuid4(),
                name=request.model_name,
                vendor="test",
                description="stub",
                specs=ModelSpecs(),
                updated_at=now,
            ),
            analysis=f"Stub analysis for {request.model_name}",
            recommendations=["Use mocked tests"],
        )

    monkeypatch.setattr(analysis_module.AnalysisService, "build_report", _fake_build_report)


@pytest.fixture
async def client() -> AsyncClient:
    """HTTP client bound to the FastAPI app (no live network)."""
    # Import after env is set so lifespan/job store pick up memory mode
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
