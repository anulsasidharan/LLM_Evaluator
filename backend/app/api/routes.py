"""REST API routes under /api/v1."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID, uuid4

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response, status

from app.api.deps import get_job_store
from app.config import get_settings
from app.models.schemas import (
    AnalysisDepth,
    AnalysisReport,
    AnalyzeRequest,
    APIResponse,
    ComparisonPayload,
    ComparisonRequest,
    ComparisonResponse,
    ExportFormat,
    HealthStatus,
    JobAccepted,
    JobResult,
    JobStatus,
    ModelProfile,
    ModelSearchHit,
    ModelSearchResponse,
    ModelSpecs,
)
from app.services.analysis_service import AnalysisService
from app.services.data_service import DataService
from app.services.job_store import JobStore
from app.services.report_service import ReportService

logger = structlog.get_logger(__name__)

router = APIRouter()

JobStoreDep = Annotated[JobStore, Depends(get_job_store)]
ExportFormatQuery = Annotated[ExportFormat, Query(alias="format")]

ESTIMATED_SECONDS_BY_DEPTH = {
    AnalysisDepth.QUICK: 45,
    AnalysisDepth.STANDARD: 90,
    AnalysisDepth.DETAILED: 150,
}


@router.get("/health", response_model=APIResponse[HealthStatus])
async def health() -> APIResponse[HealthStatus]:
    """Return API liveness information."""
    from app import __version__

    return APIResponse(data=HealthStatus(status="ok", version=__version__))


async def _run_analysis_job(job_id: UUID, payload: AnalyzeRequest, job_store: JobStore) -> None:
    """Background worker entry for a single analysis job."""
    service = AnalysisService(job_store=job_store)
    try:
        await service.start(job_id=job_id, request=payload)
    except Exception as exc:  # noqa: BLE001 — status already recorded inside service
        logger.error("background_analysis_failed", job_id=str(job_id), error=str(exc))


@router.post(
    "/models/analyze",
    response_model=APIResponse[JobAccepted],
    status_code=status.HTTP_202_ACCEPTED,
)
async def analyze_model(
    payload: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    job_store: JobStoreDep,
) -> APIResponse[JobAccepted]:
    """Queue an asynchronous model analysis job."""
    job_id = uuid4()
    estimated = ESTIMATED_SECONDS_BY_DEPTH[payload.depth]
    await job_store.create(
        job_id=job_id,
        model_name=payload.model_name,
        request=payload.model_dump(mode="json"),
    )
    logger.info(
        "analysis_job_queued",
        job_id=str(job_id),
        model_name=payload.model_name,
        depth=payload.depth.value,
    )

    settings = get_settings()
    # Memory store (unit tests): run inline so assertions can poll immediately.
    # Postgres / Docker: run in a background task so the API returns 202 quickly.
    if settings.job_store == "memory":
        await _run_analysis_job(job_id, payload, job_store)
    else:
        background_tasks.add_task(_run_analysis_job, job_id, payload, job_store)

    return APIResponse(
        data=JobAccepted(
            job_id=job_id,
            status=JobStatus.QUEUED,
            estimated_time_seconds=estimated,
            results_url=f"/api/v1/results/{job_id}",
        )
    )


@router.get("/results/{job_id}", response_model=APIResponse[JobResult])
async def get_results(
    job_id: UUID,
    job_store: JobStoreDep,
) -> APIResponse[JobResult]:
    """Poll an analysis job until it completes or fails."""
    job = await job_store.get(job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "job_not_found", "message": f"No analysis job exists for id {job_id}"},
        )

    report = None
    if job.status == JobStatus.COMPLETED and job.report is not None:
        report = AnalysisReport.model_validate(job.report)

    return APIResponse(
        data=JobResult(
            job_id=job.job_id,
            status=job.status,
            completed_at=job.completed_at,
            report=report,
        )
    )


@router.get("/models/search", response_model=APIResponse[ModelSearchResponse])
async def search_models(
    q: str = Query(..., min_length=1, max_length=256, description="Model name or tag"),
) -> APIResponse[ModelSearchResponse]:
    """Search HuggingFace models by name or tag."""
    logger.info("model_search", query=q)
    data_service = DataService()
    hits = await data_service.search_models(q, limit=15)
    results = [
        ModelSearchHit(
            id=uuid4(),
            name=str(hit.get("name") or ""),
            vendor=str(hit.get("vendor") or "unknown"),
            parameters=hit.get("parameters"),
            release_date=str(hit["release_date"]) if hit.get("release_date") else None,
            tags=list(hit.get("tags") or []),
        )
        for hit in hits
        if hit.get("name")
    ]
    return APIResponse(data=ModelSearchResponse(results=results, total=len(results)))


@router.post(
    "/comparisons",
    response_model=APIResponse[ComparisonResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_comparison(payload: ComparisonRequest) -> APIResponse[ComparisonResponse]:
    """Create a side-by-side comparison of two or more models by name lookup.

    ``modelIds`` are treated as model name strings when they are not in the local DB
    (MVP: clients may pass names cast as UUIDs is awkward — accept focus on analyze).
    For this MVP we compare via optional names encoded in focusAreas as
    ``name:<model>`` entries, or return an empty scaffold when only UUIDs are given.
    """
    comparison_id = uuid4()
    # Prefer analyzing via explicit names in focus_areas like "name:gpt-4o"
    names = [a.removeprefix("name:") for a in payload.focus_areas if a.startswith("name:")]
    models: list[ModelProfile] = []
    matrix: dict = {"benchmarks": {}, "parameters": {}, "contextWindow": {}}
    trade_offs: list[str] = []
    best_for: dict[str, str] = {}

    if len(names) >= 2:
        from datetime import UTC, datetime

        from app.services.tool_executor import ToolExecutor

        tools = ToolExecutor()
        specs_list = []
        for name in names[:4]:
            specs = await tools.execute("fetch_model_specs", {"model_name": name})
            specs_list.append(specs)
            models.append(
                ModelProfile(
                    id=uuid4(),
                    name=str(specs.get("model_name") or name),
                    vendor=str(specs.get("vendor") or "unknown"),
                    parameters=specs.get("parameters"),
                    official_url=specs.get("official_url"),
                    tags=list(specs.get("tags") or []),
                    specs=ModelSpecs(
                        context_window=specs.get("context_window"),
                        architecture=str(specs.get("architecture") or "") or None,
                        precision=list(specs.get("precision") or []),
                    ),
                    benchmarks=dict(specs.get("benchmarks") or {}),
                    updated_at=datetime.now(UTC),
                )
            )
            matrix["parameters"][name] = specs.get("parameters")
            matrix["contextWindow"][name] = specs.get("context_window")
            matrix["benchmarks"][name] = specs.get("benchmarks") or {}

        if len(names) >= 2:
            trade = await tools.execute(
                "generate_trade_off_analysis",
                {"model1": names[0], "model2": names[1]},
            )
            trade_offs = list(trade.get("trade_offs") or [])
            best_for["general"] = str(trade.get("recommendation") or names[0])

    logger.info(
        "comparison_created",
        comparison_id=str(comparison_id),
        model_count=len(payload.model_ids),
        named=len(names),
    )
    return APIResponse(
        data=ComparisonResponse(
            comparison_id=comparison_id,
            comparison=ComparisonPayload(
                models=models,
                matrix=matrix,
                best_for=best_for,
                trade_offs=trade_offs,
            ),
        )
    )


@router.get("/results/{job_id}/export")
async def export_result(
    job_id: UUID,
    job_store: JobStoreDep,
    format: ExportFormatQuery = ExportFormat.JSON,
) -> Response:
    """Export a completed analysis report as JSON or HTML."""
    job = await job_store.get(job_id)
    if job is None or job.status != JobStatus.COMPLETED or job.report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "report_not_ready",
                "message": f"Completed report not found for job {job_id}",
            },
        )
    report = AnalysisReport.model_validate(job.report)
    service = ReportService()
    payload = await service.export(report, format)
    if format == ExportFormat.JSON:
        import json

        return Response(
            content=json.dumps(payload, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="report-{job_id}.json"'},
        )
    body = payload if isinstance(payload, (bytes, bytearray)) else str(payload).encode("utf-8")
    extension = "pdf" if format == ExportFormat.PDF else "html"
    media = "application/pdf" if format == ExportFormat.PDF else "text/html"
    # PDF export currently returns print-ready HTML bytes
    if format == ExportFormat.PDF:
        media = "text/html"
        extension = "html"
    return Response(
        content=body,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="report-{job_id}.{extension}"'},
    )
