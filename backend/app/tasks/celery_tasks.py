"""Celery tasks for long-running model analysis."""

from __future__ import annotations

import asyncio
from uuid import UUID

from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "llm_evaluator",
    broker=settings.rabbitmq_url,
    backend=settings.redis_url,
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
)


@celery_app.task(name="run_analysis_job")
def run_analysis_job(job_id: str, request_payload: dict) -> None:
    """Execute an analysis job on a worker using the Postgres job store."""
    from app.api.deps import get_session_factory, reset_singletons
    from app.models.schemas import AnalyzeRequest
    from app.services.analysis_service import AnalysisService
    from app.services.db_job_store import DatabaseJobStore

    reset_singletons()
    request = AnalyzeRequest.model_validate(request_payload)
    # Workers always use Postgres so they share state with the API process
    store = DatabaseJobStore(get_session_factory())
    service = AnalysisService(job_store=store)
    asyncio.run(service.run(job_id=UUID(job_id), request=request))
