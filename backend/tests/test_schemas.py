"""Schema serialization tests (camelCase JSON, snake_case Python)."""

from datetime import UTC, datetime
from uuid import uuid4

from app.models.schemas import JobAccepted, JobStatus, ModelProfile, ModelSpecs


def test_model_profile_serializes_camel_case() -> None:
    """ModelProfile dumps JSON keys in camelCase."""
    profile = ModelProfile(
        id=uuid4(),
        name="claude-3-opus",
        vendor="Anthropic",
        parameters=None,
        official_url="https://example.com",
        specs=ModelSpecs(context_window=200000),
        updated_at=datetime.now(UTC),
    )
    payload = profile.model_dump(by_alias=True)
    assert "officialUrl" in payload
    assert "updatedAt" in payload
    assert payload["specs"]["contextWindow"] == 200000
    assert "official_url" not in payload


def test_job_accepted_parses_camel_case_input() -> None:
    """JobAccepted accepts camelCase input via aliases."""
    job_id = uuid4()
    parsed = JobAccepted.model_validate(
        {
            "jobId": str(job_id),
            "status": "queued",
            "estimatedTimeSeconds": 30,
            "resultsUrl": f"/api/v1/results/{job_id}",
        }
    )
    assert parsed.job_id == job_id
    assert parsed.status == JobStatus.QUEUED
    assert parsed.estimated_time_seconds == 30
