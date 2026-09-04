# LLM Model Evaluator

Analytical platform for comparing and evaluating large language models — benchmarks, capabilities, and hosting requirements.

## Stack

- **Backend**: Python 3.11+, FastAPI, PostgreSQL, Redis, Celery
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS
- **LLM**: OpenAI (primary when keyed), Anthropic and Google fallbacks
- **Data**: HuggingFace Hub, Ollama library, ArXiv

## Quick start (Docker Compose — recommended)

```bash
cp .env.example .env
# Put your OPENAI_API_KEY in .env
docker compose up --build
```

- UI: http://localhost:3002  
- API: http://localhost:8002  
- Docs: http://localhost:8002/docs  

Enter a model name such as `meta-llama/Llama-3.1-8B-Instruct` or `mistralai/Mistral-7B-Instruct-v0.2`.

## Local development (without Docker for the apps)

```bash
cp .env.example .env
# start postgres/redis via: docker compose up postgres redis -d

cd backend
uv sync --extra dev
# JOB_STORE=memory for quick local API without Postgres, or postgres with DB up
uv run uvicorn app.main:app --reload --port 8002

cd frontend
npm install
npm run dev
```

## Tests

```bash
cd backend && uv run pytest
cd frontend && npm test
```

## Project layout

```
backend/app/     FastAPI application, tools, integrations
frontend/src/   Next.js App Router UI
docs/           Architecture, API, data sources, deployment
```

Full specification: [CLAUDE.md](./CLAUDE.md)
