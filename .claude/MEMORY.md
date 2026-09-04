# LLM Model Evaluator — Project Memory

## Project Status
- **Phase**: Phase 1 MVP — Docker Compose full stack with live HF/Ollama/ArXiv + OpenAI synthesis
- **Created**: 2026-09-03
- **Stack**: Python 3.11+ (FastAPI) backend, Next.js 14+ (TypeScript) frontend
- **Database**: PostgreSQL 15+ with Redis 7+ cache
- **Primary LLM**: OpenAI when keyed; Anthropic / Google as fallbacks

## Key Architecture Decisions
- Tool-calling + deterministic gather → OpenAI JSON synthesis
- Async analysis jobs in FastAPI BackgroundTasks, persisted in Postgres
- Multi-source data pipeline: HuggingFace, Ollama, ArXiv
- Ports: UI `3002`, API `8002` (avoid 3000/8000)
- Report formats: JSON + HTML export

## Directory Structure
- `backend/app/` — FastAPI application
- `frontend/src/` — Next.js application
- `CLAUDE.md` — Full project specification and architecture

## Build & Run Commands
- Docker: `docker compose up --build` from project root
- Backend: `cd backend && uv sync --extra dev && uv run uvicorn app.main:app --reload --port 8002`
- Frontend: `npm run dev` (from `frontend/`, port 3002)
- Tests: `cd backend && uv run pytest` and `npm test` (from `frontend/`)

## Important Patterns
- All benchmark scores normalized to 0–100 scale
- Model parameter counts stored as integers
- camelCase in JSON, snake_case in Python, PascalCase for types/interfaces
- External API calls always have timeouts and retry logic
- Secrets only in `.env` (never commit)
