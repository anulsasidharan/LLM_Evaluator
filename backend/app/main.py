"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import __version__
from app.api.deps import get_engine
from app.api.routes import router
from app.config import get_settings
from app.integrations import list_sources  # noqa: F401  registers data sources
from app.logging import configure_logging
from app.models.database import Base
from app.models.schemas import APIResponse, ErrorDetail, HealthStatus

settings = get_settings()
configure_logging(debug=settings.debug)
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Create database tables on startup when using Postgres job store."""
    cfg = get_settings()
    if cfg.job_store != "memory":
        engine = get_engine(cfg)
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("database_schema_ready")
        except Exception as exc:  # noqa: BLE001
            logger.error("database_schema_failed", error=str(exc))
            raise
    logger.info(
        "app_started",
        job_store=cfg.job_store,
        sources=list_sources(),
        llm_providers=[
            name
            for name, key in (
                ("anthropic", cfg.anthropic_api_key),
                ("openai", cfg.openai_api_key),
                ("google", cfg.google_api_key),
            )
            if key
        ],
    )
    yield


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix=settings.api_prefix)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Wrap HTTP errors in the standard API envelope."""
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail and "message" in detail:
        error = ErrorDetail(code=str(detail["code"]), message=str(detail["message"]))
    else:
        error = ErrorDetail(code="http_error", message=str(detail))
    body = APIResponse[None](data=None, error=error)
    return JSONResponse(
        status_code=exc.status_code,
        content=body.model_dump(mode="json", by_alias=True),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return structured 422 errors with field paths."""
    messages = "; ".join(
        f"{'.'.join(str(loc) for loc in err.get('loc', []))}: {err.get('msg')}"
        for err in exc.errors()
    )
    body = APIResponse[None](
        data=None,
        error=ErrorDetail(code="validation_error", message=messages),
    )
    return JSONResponse(
        status_code=422,
        content=body.model_dump(mode="json", by_alias=True),
    )


@app.get("/", response_model=APIResponse[HealthStatus])
async def root() -> APIResponse[HealthStatus]:
    """Root liveness probe (also available at /api/v1/health)."""
    return APIResponse(data=HealthStatus(status="ok", version=__version__))
