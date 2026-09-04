"""Estimate local / cloud hosting resource requirements from model size."""

from __future__ import annotations

from uuid import uuid4

from app.models.schemas import (
    DeploymentType,
    HardwareTier,
    HostingOption,
    ResourceRequirement,
    ResourceTiers,
)

# Bytes per parameter for common precisions
BYTES_PER_PARAM = {
    "fp32": 4.0,
    "fp16": 2.0,
    "bf16": 2.0,
    "int8": 1.0,
    "int4": 0.5,
}


def estimate_gpu_memory_gb(parameters: int | None, precision: str = "fp16") -> float | None:
    """Rough VRAM estimate: params * bytes + 20% overhead."""
    if parameters is None or parameters <= 0:
        return None
    bpp = BYTES_PER_PARAM.get(precision.lower(), 2.0)
    return round((parameters * bpp) / (1024**3) * 1.2, 1)


def calculate_resource_requirements(
    *,
    model_id: None | object = None,
    parameters: int | None,
    deployment_type: DeploymentType = DeploymentType.LOCAL,
    ollama_available: bool = False,
    precision: str = "fp16",
) -> ResourceRequirement:
    """Build min/optimal/max resource tiers from parameter count."""
    from uuid import UUID

    mid = model_id if isinstance(model_id, UUID) else uuid4()
    base = estimate_gpu_memory_gb(parameters, precision) or 8.0

    minimum = HardwareTier(
        gpu_memory=f"{max(4, round(base * 0.5))}GB",
        cpu_cores=4 if base < 20 else 8,
        ram_gb=max(16, int(base)),
        storage_ssd="50GB",
        inference_time="slow / quantized",
    )
    optimal = HardwareTier(
        gpu_memory=f"{max(8, round(base))}GB",
        cpu_cores=8 if base < 40 else 16,
        ram_gb=max(32, int(base * 1.5)),
        storage_ssd="100GB",
        inference_time="interactive",
    )
    maximum = HardwareTier(
        gpu_memory=f"{max(16, round(base * 2))}GB",
        cpu_cores=16 if base < 40 else 32,
        ram_gb=max(64, int(base * 2)),
        storage_ssd="200GB",
        inference_time="high-throughput",
    )

    hosting = HostingOption.OLLAMA if ollama_available else HostingOption.VLLM
    if deployment_type == DeploymentType.CLOUD:
        hosting = HostingOption.VLLM

    return ResourceRequirement(
        id=uuid4(),
        model_id=mid,
        deployment_type=deployment_type,
        hosting_option=hosting,
        requirements=ResourceTiers(minimum=minimum, optimal=optimal, maximum=maximum),
    )
