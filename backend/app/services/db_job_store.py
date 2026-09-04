"""PostgreSQL-backed analysis job store."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.database import AnalysisJobRow
from app.models.schemas import JobStatus
from app.services.job_store import StoredJob


class DatabaseJobStore:
    """Persists analysis jobs in PostgreSQL for multi-process Docker use."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def create(self, job_id: UUID, model_name: str, request: dict[str, Any]) -> StoredJob:
        """Insert a queued job."""
        async with self._session_factory() as session:
            row = AnalysisJobRow(
                id=job_id,
                model_name=model_name,
                status=JobStatus.QUEUED.value,
                request_payload=request,
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)
            return self._to_stored(row)

    async def get(self, job_id: UUID) -> StoredJob | None:
        """Fetch a job by id, or None if missing."""
        async with self._session_factory() as session:
            row = await session.get(AnalysisJobRow, job_id)
            return self._to_stored(row) if row else None

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
        async with self._session_factory() as session:
            row = await session.get(AnalysisJobRow, job_id)
            if row is None:
                return None
            if status is not None:
                row.status = status.value
            if report is not None:
                row.report_data = report
            if error_message is not None:
                row.error_message = error_message
            if completed_at is not None:
                row.completed_at = completed_at
            await session.commit()
            await session.refresh(row)
            return self._to_stored(row)

    async def list_recent(self, *, limit: int = 20) -> list[StoredJob]:
        """Return recent jobs for debugging / admin."""
        async with self._session_factory() as session:
            result = await session.execute(
                select(AnalysisJobRow).order_by(AnalysisJobRow.created_at.desc()).limit(limit)
            )
            return [self._to_stored(row) for row in result.scalars().all()]

    @staticmethod
    def _to_stored(row: AnalysisJobRow) -> StoredJob:
        return StoredJob(
            job_id=row.id if isinstance(row.id, UUID) else UUID(str(row.id)),
            model_name=row.model_name,
            status=JobStatus(row.status),
            request=dict(row.request_payload or {}),
            report=dict(row.report_data) if row.report_data else None,
            error_message=row.error_message,
            created_at=row.created_at,
            completed_at=row.completed_at,
        )
