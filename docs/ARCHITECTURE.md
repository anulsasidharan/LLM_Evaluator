# Architecture

See `CLAUDE.md` section 2–3 for the full system design.

This document tracks implementation notes for the running scaffold:

- **API**: FastAPI app in `backend/app/main.py`, routes under `/api/v1/`
- **Jobs**: In-memory `JobStore` by default (`USE_CELERY=false`). Celery + RabbitMQ is wired but unused until a shared store (Redis/Postgres) is connected
- **Data sources**: Register implementations of `DataSourceInterface` in `backend/app/integrations/`
- **LLM**: `LLMService` loads prompts from `backend/app/prompts/` and will call Anthropic → OpenAI → Google
