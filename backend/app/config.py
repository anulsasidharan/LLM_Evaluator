"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the API server, cache, and LLM providers."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "LLM Model Evaluator"
    debug: bool = False
    api_prefix: str = "/api/v1"

    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/llm_evaluator"
    )
    redis_url: str = "redis://localhost:6379/0"
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672//"

    cors_origins: str = "http://localhost:3002"

    anthropic_api_key: str = ""
    openai_api_key: str = ""
    google_api_key: str = ""
    huggingface_api_token: str = ""

    llm_timeout_seconds: int = 60
    http_timeout_seconds: int = 30
    http_max_retries: int = 3

    cache_ttl_model_profile_seconds: int = Field(default=7 * 24 * 3600)
    cache_ttl_benchmark_seconds: int = Field(default=3 * 24 * 3600)
    cache_ttl_report_seconds: int = Field(default=24 * 3600)
    cache_ttl_llm_analysis_seconds: int = Field(default=24 * 3600)

    use_celery: bool = False
    # "memory" for local/unit tests; "postgres" for Docker / production
    job_store: str = "postgres"
    openai_model: str = "gpt-4o-mini"

    def cors_origin_list(self) -> list[str]:
        """Return CORS origins as a list of stripped URLs."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
