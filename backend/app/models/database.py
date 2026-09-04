"""SQLAlchemy ORM models matching the core data entities."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


class ModelProfileRow(Base):
    """Persisted LLM profile."""

    __tablename__ = "model_profiles"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(256), unique=True, index=True)
    vendor: Mapped[str] = mapped_column(String(128), index=True)
    version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    parameters: Mapped[int | None] = mapped_column(Integer, nullable=True)
    release_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    official_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    tags: Mapped[list] = mapped_column(JSONB, default=list)
    specs: Mapped[dict] = mapped_column(JSONB, default=dict)
    benchmarks: Mapped[dict] = mapped_column(JSONB, default=dict)
    capabilities: Mapped[dict] = mapped_column(JSONB, default=dict)
    flaws: Mapped[list] = mapped_column(JSONB, default=list)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    benchmark_results: Mapped[list["BenchmarkResultRow"]] = relationship(back_populates="model")
    resource_requirements: Mapped[list["ResourceRequirementRow"]] = relationship(
        back_populates="model"
    )


class BenchmarkResultRow(Base):
    """Persisted benchmark score with provenance."""

    __tablename__ = "benchmark_results"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    model_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("model_profiles.id"), index=True
    )
    benchmark_name: Mapped[str] = mapped_column(String(128), index=True)
    score: Mapped[float | None] = mapped_column(nullable=True)
    percentile: Mapped[float | None] = mapped_column(nullable=True)
    source: Mapped[str] = mapped_column(String(64))
    source_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    extra_metadata: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    model: Mapped[ModelProfileRow] = relationship(back_populates="benchmark_results")


class ResourceRequirementRow(Base):
    """Persisted hosting requirements for a model."""

    __tablename__ = "resource_requirements"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    model_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("model_profiles.id"), index=True
    )
    deployment_type: Mapped[str] = mapped_column(String(32))
    hosting_option: Mapped[str | None] = mapped_column(String(32), nullable=True)
    requirements: Mapped[dict] = mapped_column(JSONB, default=dict)

    model: Mapped[ModelProfileRow] = relationship(back_populates="resource_requirements")


class ComparisonReportRow(Base):
    """Persisted comparison report with TTL metadata."""

    __tablename__ = "comparison_reports"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    models_compared: Mapped[list] = mapped_column(JSONB, default=list)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    report_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    export_formats: Mapped[list] = mapped_column(JSONB, default=list)


class AnalysisJobRow(Base):
    """Persisted async analysis job for polling."""

    __tablename__ = "analysis_jobs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    model_name: Mapped[str] = mapped_column(String(256), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True, default="queued")
    request_payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    report_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    token_usage: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
