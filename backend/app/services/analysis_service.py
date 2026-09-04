"""Orchestrates data gathering + LLM synthesis into an AnalysisReport."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import structlog

from app.config import get_settings
from app.models.schemas import (
    AnalysisReport,
    AnalyzeRequest,
    BenchmarkResult,
    JobStatus,
    ModelProfile,
    ModelSpecs,
    ResourceRequirement,
)
from app.services.job_store import JobStore
from app.services.llm_service import LLMService
from app.services.tool_executor import ToolExecutor

logger = structlog.get_logger(__name__)


class AnalysisService:
    """Runs model analysis: gather tools → synthesize with LLM → persist report."""

    def __init__(
        self,
        job_store: JobStore,
        llm_service: LLMService | None = None,
        tool_executor: ToolExecutor | None = None,
    ) -> None:
        self._job_store = job_store
        self._settings = get_settings()
        self._tools = tool_executor or ToolExecutor()
        self._llm = llm_service or LLMService(tool_executor=self._tools)

    async def start(self, job_id: UUID, request: AnalyzeRequest) -> None:
        """Mark the job processing. Prefer in-process run; Celery when enabled."""
        if self._settings.use_celery:
            from app.tasks.celery_tasks import run_analysis_job

            run_analysis_job.delay(str(job_id), request.model_dump(mode="json"))
            return

        await self.run(job_id=job_id, request=request)

    async def run(self, job_id: UUID, request: AnalyzeRequest) -> None:
        """Execute analysis and persist the completed report."""
        await self._job_store.update(job_id, status=JobStatus.PROCESSING)
        logger.info("analysis_started", job_id=str(job_id), model_name=request.model_name)

        try:
            report = await self.build_report(request)
            await self._job_store.update(
                job_id,
                status=JobStatus.COMPLETED,
                report=report.model_dump(mode="json"),
                completed_at=datetime.now(UTC),
            )
            logger.info("analysis_completed", job_id=str(job_id), model_name=request.model_name)
        except Exception as exc:
            logger.error(
                "analysis_failed",
                job_id=str(job_id),
                model_name=request.model_name,
                error=str(exc),
            )
            await self._job_store.update(
                job_id,
                status=JobStatus.FAILED,
                error_message=str(exc),
                completed_at=datetime.now(UTC),
            )
            raise

    async def build_report(self, request: AnalyzeRequest) -> AnalysisReport:
        """Gather live data and synthesize an AnalysisReport."""
        model_name = request.model_name.strip()
        gathered = await self._tools.gather_for_model(model_name)

        # Optional competitor trade-offs when compare_with provided
        trade_offs: list[str] = []
        for other in request.compare_with[:3]:
            result = await self._tools.execute(
                "generate_trade_off_analysis",
                {"model1": model_name, "model2": other},
            )
            trade_offs.extend(result.get("trade_offs") or [])

        synthesis = await self._llm.synthesize_report_json(
            model_name=model_name,
            gathered={**gathered, "trade_offs": trade_offs},
        )

        return self._assemble_report(model_name, gathered, synthesis, request)

    def _assemble_report(
        self,
        model_name: str,
        gathered: dict,
        synthesis: dict,
        request: AnalyzeRequest,
    ) -> AnalysisReport:
        now = datetime.now(UTC)
        specs_data = gathered.get("specs") or {}
        capabilities_data = gathered.get("capabilities") or {}
        benchmarks_data = gathered.get("benchmarks") or {}
        resources_data = gathered.get("resources") or {}
        competitors_data = gathered.get("competitors") or {}

        model_id = uuid4()
        architecture = specs_data.get("architecture")
        if isinstance(architecture, list):
            architecture = ", ".join(str(a) for a in architecture)

        precision = specs_data.get("precision") or []
        if not isinstance(precision, list):
            precision = [str(precision)]

        profile = ModelProfile(
            id=model_id,
            name=str(specs_data.get("model_name") or model_name),
            vendor=str(specs_data.get("vendor") or "unknown"),
            parameters=specs_data.get("parameters"),
            description=str(specs_data.get("description") or synthesis.get("summary") or ""),
            official_url=specs_data.get("official_url"),
            tags=list(specs_data.get("tags") or []),
            specs=ModelSpecs(
                context_window=specs_data.get("context_window"),
                architecture=str(architecture) if architecture else None,
                precision=[str(p) for p in precision],
            ),
            benchmarks=dict(specs_data.get("benchmarks") or benchmarks_data.get("metrics") or {}),
            capabilities=dict(synthesis.get("capabilities") or {}),
            flaws=list(synthesis.get("flaws") or capabilities_data.get("weaknesses") or []),
            updated_at=now,
        )

        benchmark_rows: list[BenchmarkResult] = []
        for row in benchmarks_data.get("benchmarks") or []:
            if not isinstance(row, dict):
                continue
            benchmark_rows.append(
                BenchmarkResult(
                    id=uuid4(),
                    model_id=model_id,
                    benchmark_name=str(row.get("benchmark_name") or "unknown"),
                    score=row.get("score"),
                    source=str(row.get("source") or "huggingface"),
                    source_url=row.get("source_url"),
                    recorded_at=now,
                )
            )

        resources: ResourceRequirement | None = None
        if request.include_resources and resources_data.get("requirement"):
            try:
                resources = ResourceRequirement.model_validate(resources_data["requirement"])
            except Exception:  # noqa: BLE001
                resources = None

        competitors = list(
            synthesis.get("competitors")
            or competitors_data.get("competitors")
            or []
        )
        recommendations = list(synthesis.get("recommendations") or [])
        analysis_text = str(synthesis.get("analysis") or synthesis.get("summary") or "")

        # Enrich analysis with source provenance notes
        notes = []
        if benchmarks_data.get("source_notes"):
            notes.extend(benchmarks_data["source_notes"])
        if specs_data.get("source_url"):
            notes.append(f"Primary model card: {specs_data['source_url']}")
        ollama = specs_data.get("ollama") or {}
        if ollama.get("available_on_ollama"):
            notes.append(f"Available on Ollama: {ollama.get('official_url') or ollama.get('name')}")
        papers = (gathered.get("papers") or {}).get("papers") or []
        if papers:
            notes.append(f"Related papers found: {len(papers)}")
        if notes:
            analysis_text = (analysis_text + "\n\nSources:\n- " + "\n- ".join(notes)).strip()

        return AnalysisReport(
            model=profile,
            benchmarks=benchmark_rows,
            capabilities=dict(synthesis.get("capabilities") or capabilities_data),
            flaws=list(profile.flaws),
            competitors=[str(c) for c in competitors],
            resources=resources,
            analysis=analysis_text,
            recommendations=recommendations,
        )
