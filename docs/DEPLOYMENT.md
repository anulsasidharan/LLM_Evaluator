# Deployment

## Docker Compose (recommended)

```bash
cp .env.example .env
# Set OPENAI_API_KEY (and optionally HUGGINGFACE_API_TOKEN)
docker compose up --build
```

| Service | URL |
|---------|-----|
| Web UI | http://localhost:3002 |
| API | http://localhost:8002 |
| API docs | http://localhost:8002/docs |
| Postgres (host) | localhost:5433 |
| Redis (host) | localhost:6380 |
| RabbitMQ management | http://localhost:15673 |

The API creates tables on startup (`JOB_STORE=postgres`). Analysis jobs run in FastAPI background tasks and persist to Postgres.

## Local (apps outside Docker)

1. `docker compose up postgres redis -d`
2. Backend: `cd backend && uv sync --extra dev && uv run uvicorn app.main:app --reload --port 8002`
3. Frontend: `cd frontend && npm install && npm run dev`
4. Open http://localhost:3002 — API at http://localhost:8002
