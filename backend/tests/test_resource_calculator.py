"""Resource calculator unit tests."""

from app.models.schemas import DeploymentType
from app.services.resource_calculator import calculate_resource_requirements, estimate_gpu_memory_gb


def test_estimate_gpu_memory_scales_with_parameters() -> None:
    """Larger models need more VRAM."""
    small = estimate_gpu_memory_gb(7_000_000_000, "fp16")
    large = estimate_gpu_memory_gb(70_000_000_000, "fp16")
    assert small is not None and large is not None
    assert large > small


def test_calculate_resource_requirements_sets_tiers() -> None:
    """Resource tiers include GPU memory strings."""
    req = calculate_resource_requirements(
        parameters=8_000_000_000,
        deployment_type=DeploymentType.LOCAL,
        ollama_available=True,
    )
    assert req.hosting_option is not None
    assert req.requirements.minimum.gpu_memory
    assert req.requirements.optimal.gpu_memory
