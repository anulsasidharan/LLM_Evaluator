"""Shared API dependencies."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings, get_settings
from app.services.db_job_store import DatabaseJobStore
from app.services.job_store import InMemoryJobStore, JobStore

_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None
_job_store: JobStore | None = None


def get_engine(settings: Settings | None = None):
    """Create (or reuse) the async SQLAlchemy engine."""
    global _engine
    if _engine is None:
        cfg = settings or get_settings()
        _engine = create_async_engine(cfg.database_url, pool_pre_ping=True)
    return _engine


def get_session_factory(settings: Settings | None = None) -> async_sessionmaker[AsyncSession]:
    """Return the async session factory."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(get_engine(settings), expire_on_commit=False)
    return _session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a request-scoped database session."""
    factory = get_session_factory()
    async with factory() as session:
        yield session


def reset_singletons() -> None:
    """Reset cached engine/session/job-store (used in tests)."""
    global _engine, _session_factory, _job_store
    _engine = None
    _session_factory = None
    _job_store = None


def get_job_store() -> JobStore:
    """Return the configured job store (Postgres by default, memory for tests)."""
    global _job_store
    if _job_store is None:
        settings = get_settings()
        if settings.job_store == "memory":
            _job_store = InMemoryJobStore()
        else:
            _job_store = DatabaseJobStore(get_session_factory(settings))
    return _job_store
