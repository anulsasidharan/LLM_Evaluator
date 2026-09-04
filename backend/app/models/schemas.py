"""Pydantic request/response schemas. JSON fields use camelCase aliases."""

from datetime import datetime
from enum import StrEnum
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class APIModel(BaseModel):
    """Base model that serializes to camelCase JSON while accepting snake_case."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


T = TypeVar("T")


class ErrorDetail(APIModel):
    """Structured API error payload."""

    code: str
    message: str


class APIResponse(APIModel, Generic[T]):
    """Standard API envelope used by every endpoint."""

    data: T | None = None
    error: ErrorDetail | None = None


class AnalysisDepth(StrEnum):
    """How thoroughly to analyze a model."""

    QUICK = "quick"
    STANDARD = "standard"
    DETAILED = "detailed"


class ExportFormat(StrEnum):
    """Supported report export formats."""

    JSON = "json"
    PDF = "pdf"
    HTML = "html"


class JobStatus(StrEnum):
    """Async analysis job lifecycle."""

    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DeploymentType(StrEnum):
    """Where a model can be hosted."""

    LOCAL = "local"
    CLOUD = "cloud"
    EDGE = "edge"


class HostingOption(StrEnum):
    """Local/self-hosted inference runtimes."""

    OLLAMA = "ollama"
    VLLM = "vllm"
    LLAMA_CPP = "llama.cpp"


class ModelSpecs(APIModel):
    """Technical specifications for a model."""

    context_window: int | None = None
    training_data_cutoff: str | None = None
    architecture: str | None = None
    precision: list[str] = Field(default_factory=list)


class ModelProfile(APIModel):
    """Canonical profile of an LLM."""

    id: UUID
    name: str
    vendor: str
    version: str | None = None
    parameters: int | None = None
    release_date: str | None = None
    description: str = ""
    official_url: str | None = None
    tags: list[str] = Field(default_factory=list)
    specs: ModelSpecs = Field(default_factory=ModelSpecs)
    benchmarks: dict[str, Any] = Field(default_factory=dict)
    capabilities: dict[str, Any] = Field(default_factory=dict)
    flaws: list[str] = Field(default_factory=list)
    updated_at: datetime


class BenchmarkResult(APIModel):
    """A single benchmark score for a model."""

    id: UUID
    model_id: UUID
    benchmark_name: str
    score: float | None = None
    percentile: float | None = None
    source: str
    source_url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    recorded_at: datetime


class HardwareTier(APIModel):
    """Resource numbers for one deployment tier (min/optimal/max)."""

    gpu_memory: str | None = None
    cpu_cores: int | None = None
    ram_gb: int | None = None
    storage_ssd: str | None = None
    inference_time: str | None = None


class ResourceTiers(APIModel):
    """Minimum, optimal, and maximum resource envelopes."""

    minimum: HardwareTier = Field(default_factory=HardwareTier)
    optimal: HardwareTier = Field(default_factory=HardwareTier)
    maximum: HardwareTier = Field(default_factory=HardwareTier)


class ResourceRequirement(APIModel):
    """Hosting requirements for a model under a deployment type."""

    id: UUID
    model_id: UUID
    deployment_type: DeploymentType
    hosting_option: HostingOption | None = None
    requirements: ResourceTiers = Field(default_factory=ResourceTiers)


class AnalyzeRequest(APIModel):
    """Request body for POST /models/analyze."""

    model_name: str = Field(..., min_length=1, max_length=256)
    depth: AnalysisDepth = AnalysisDepth.STANDARD
    compare_with: list[str] = Field(default_factory=list)
    include_resources: bool = True
    export_format: ExportFormat = ExportFormat.JSON


class JobAccepted(APIModel):
    """Immediate response when an analysis job is queued."""

    job_id: UUID
    status: JobStatus
    estimated_time_seconds: int
    results_url: str


class ModelSearchHit(APIModel):
    """A lightweight search result row."""

    id: UUID
    name: str
    vendor: str
    parameters: int | None = None
    release_date: str | None = None
    tags: list[str] = Field(default_factory=list)


class ModelSearchResponse(APIModel):
    """Paginated model search results."""

    results: list[ModelSearchHit]
    total: int


class AnalysisReport(APIModel):
    """Completed analysis payload returned by GET /results/{jobId}."""

    model: ModelProfile | None = None
    benchmarks: list[BenchmarkResult] = Field(default_factory=list)
    capabilities: dict[str, Any] = Field(default_factory=dict)
    flaws: list[str] = Field(default_factory=list)
    competitors: list[str] = Field(default_factory=list)
    resources: ResourceRequirement | None = None
    analysis: str = ""
    recommendations: list[str] = Field(default_factory=list)


class JobResult(APIModel):
    """Status plus optional report for an analysis job."""

    job_id: UUID
    status: JobStatus
    completed_at: datetime | None = None
    report: AnalysisReport | None = None


class ComparisonRequest(APIModel):
    """Request body for POST /comparisons."""

    model_ids: list[UUID] = Field(..., min_length=2)
    focus_areas: list[str] = Field(default_factory=lambda: ["capabilities", "speed", "cost"])


class ComparisonPayload(APIModel):
    """Structured side-by-side comparison."""

    models: list[ModelProfile] = Field(default_factory=list)
    matrix: dict[str, Any] = Field(default_factory=dict)
    best_for: dict[str, str] = Field(default_factory=dict)
    trade_offs: list[str] = Field(default_factory=list)


class ComparisonResponse(APIModel):
    """Response for a newly created comparison."""

    comparison_id: UUID
    comparison: ComparisonPayload


class HealthStatus(APIModel):
    """Liveness payload for GET /health."""

    status: str
    version: str
