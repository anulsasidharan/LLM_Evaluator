"""LLM tool definitions with Pydantic input/output schemas.

Each tool is idempotent and safe to retry. Implementations live in services
and integrations; this module only describes the contracts the LLM can call.
"""

from enum import StrEnum
from typing import Any

from pydantic import Field

from app.models.schemas import APIModel, DeploymentType


class BenchmarkType(StrEnum):
    """High-level benchmark categories the search tool can filter on."""

    REASONING = "reasoning"
    KNOWLEDGE = "knowledge"
    CODING = "coding"
    MATH = "math"
    MULTIMODAL = "multimodal"
    ALL = "all"


class SearchBenchmarksInput(APIModel):
    """Arguments for search_benchmarks."""

    model_name: str = Field(..., min_length=1)
    benchmark_type: BenchmarkType = BenchmarkType.ALL


class SearchBenchmarksOutput(APIModel):
    """Normalized benchmark scores for a model."""

    model_name: str
    benchmarks: list[dict[str, Any]] = Field(default_factory=list)
    source_notes: list[str] = Field(default_factory=list)


class FetchModelSpecsInput(APIModel):
    """Arguments for fetch_model_specs."""

    model_name: str = Field(..., min_length=1)


class FetchModelSpecsOutput(APIModel):
    """Technical specifications extracted from vendor/HF sources."""

    model_name: str
    vendor: str | None = None
    parameters: int | None = None
    context_window: int | None = None
    architecture: str | None = None
    precision: list[str] = Field(default_factory=list)
    official_url: str | None = None


class AnalyzeCapabilitiesInput(APIModel):
    """Arguments for analyze_capabilities."""

    model_name: str = Field(..., min_length=1)


class AnalyzeCapabilitiesOutput(APIModel):
    """Structured strengths, weaknesses, and use cases."""

    model_name: str
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    ideal_use_cases: list[str] = Field(default_factory=list)
    poor_use_cases: list[str] = Field(default_factory=list)


class FindCompetitorsInput(APIModel):
    """Arguments for find_competitors."""

    model_name: str = Field(..., min_length=1)
    category: str = "general"


class FindCompetitorsOutput(APIModel):
    """Comparable models in the same category."""

    model_name: str
    competitors: list[str] = Field(default_factory=list)


class CalculateResourceRequirementsInput(APIModel):
    """Arguments for calculate_resource_requirements."""

    model_name: str = Field(..., min_length=1)
    deployment_type: DeploymentType = DeploymentType.LOCAL


class CalculateResourceRequirementsOutput(APIModel):
    """Estimated hosting requirements."""

    model_name: str
    deployment_type: DeploymentType
    gpu_memory_gb_minimum: float | None = None
    gpu_memory_gb_optimal: float | None = None
    notes: list[str] = Field(default_factory=list)


class GenerateTradeOffAnalysisInput(APIModel):
    """Arguments for generate_trade_off_analysis."""

    model1: str = Field(..., min_length=1)
    model2: str = Field(..., min_length=1)


class GenerateTradeOffAnalysisOutput(APIModel):
    """Qualitative trade-offs between two models."""

    model1: str
    model2: str
    trade_offs: list[str] = Field(default_factory=list)
    recommendation: str = ""


class FetchResearchPapersInput(APIModel):
    """Arguments for fetch_research_papers."""

    model_name: str = Field(..., min_length=1)
    topic: str = "architecture"


class FetchResearchPapersOutput(APIModel):
    """ArXiv / paper references for a model."""

    model_name: str
    papers: list[dict[str, Any]] = Field(default_factory=list)


class ExtractPerformanceMetricsInput(APIModel):
    """Arguments for extract_performance_metrics."""

    model_name: str = Field(..., min_length=1)


class ExtractPerformanceMetricsOutput(APIModel):
    """Normalized 0–100 performance metrics."""

    model_name: str
    metrics: dict[str, float | None] = Field(default_factory=dict)


TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "search_benchmarks",
        "description": "Fetch official and HuggingFace benchmark scores for a model.",
        "input_schema": SearchBenchmarksInput,
        "output_schema": SearchBenchmarksOutput,
    },
    {
        "name": "fetch_model_specs",
        "description": "Get technical specifications (parameters, context, architecture).",
        "input_schema": FetchModelSpecsInput,
        "output_schema": FetchModelSpecsOutput,
    },
    {
        "name": "analyze_capabilities",
        "description": "Extract capability claims, strengths, and known limitations.",
        "input_schema": AnalyzeCapabilitiesInput,
        "output_schema": AnalyzeCapabilitiesOutput,
    },
    {
        "name": "find_competitors",
        "description": "Identify comparable models in the same category.",
        "input_schema": FindCompetitorsInput,
        "output_schema": FindCompetitorsOutput,
    },
    {
        "name": "calculate_resource_requirements",
        "description": "Compute hosting needs for local, cloud, or edge deployment.",
        "input_schema": CalculateResourceRequirementsInput,
        "output_schema": CalculateResourceRequirementsOutput,
    },
    {
        "name": "generate_trade_off_analysis",
        "description": "Compare two models and summarize key trade-offs.",
        "input_schema": GenerateTradeOffAnalysisInput,
        "output_schema": GenerateTradeOffAnalysisOutput,
    },
    {
        "name": "fetch_research_papers",
        "description": "Find academic papers related to a model and topic.",
        "input_schema": FetchResearchPapersInput,
        "output_schema": FetchResearchPapersOutput,
    },
    {
        "name": "extract_performance_metrics",
        "description": "Parse and normalize performance scores onto a 0–100 scale.",
        "input_schema": ExtractPerformanceMetricsInput,
        "output_schema": ExtractPerformanceMetricsOutput,
    },
]


def get_available_tools() -> list[dict[str, Any]]:
    """Return tool metadata for LLM providers (name, description, JSON schema)."""
    tools: list[dict[str, Any]] = []
    for definition in TOOL_DEFINITIONS:
        input_schema = definition["input_schema"]
        tools.append(
            {
                "name": definition["name"],
                "description": definition["description"],
                "input_schema": input_schema.model_json_schema(),
            }
        )
    return tools
