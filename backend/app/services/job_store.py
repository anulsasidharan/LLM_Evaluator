"""In-memory job store used until Redis-backed persistence is wired up."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import UUID

from app.models.schemas import JobStatus


@dataclass
class StoredJob:
    """Internal representation of an analysis job."""

    job_id: UUID
    model_name: str
    status: JobStatus
    request: dict[str, Any]
    report: dict[str, Any] | None = None
    error_message: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None


class JobStore(Protocol):
    """Persistence interface for analysis jobs."""

    async def create(self, job_id: UUID, model_name: str, request: dict[str, Any]) -> StoredJob:
        """Insert a queued job."""
        ...

    async def get(self, job_id: UUID) -> StoredJob | None:
        """Fetch a job by id, or None if missing."""
        ...

    async def update(
        self,
        job_id: UUID,
        *,
        status: JobStatus | None = None,
        report: dict[str, Any] | None = None,
        error_message: str | None = None,
        completed_at: datetime | None = None,
    ) -> StoredJob | None:
        """Patch job fields. Returns the updated job or None if missing."""
        ...


class InMemoryJobStore:
    """Process-local job store suitable for local development and tests."""

    def __init__(self) -> None:
        self._jobs: dict[UUID, StoredJob] = {}

    async def create(self, job_id: UUID, model_name: str, request: dict[str, Any]) -> StoredJob:
        """Insert a queued job."""
        job = StoredJob(
            job_id=job_id,
            model_name=model_name,
            status=JobStatus.QUEUED,
            request=request,
        )
        self._jobs[job_id] = job
        return job

    async def get(self, job_id: UUID) -> StoredJob | None:
        """Fetch a job by id, or None if missing."""
        return self._jobs.get(job_id)

    async def update(
        self,
        job_id: UUID,
        *,
        status: JobStatus | None = None,
        report: dict[str, Any] | None = None,
        error_message: str | None = None,
        completed_at: datetime | None = None,
    ) -> StoredJob | None:
        """Patch job fields. Returns the updated job or None if missing."""
        job = self._jobs.get(job_id)
        if job is None:
            return None
        if status is not None:
            job.status = status
        if report is not None:
            job.report = report
        if error_message is not None:
            job.error_message = error_message
        if completed_at is not None:
            job.completed_at = completed_at
        return job
