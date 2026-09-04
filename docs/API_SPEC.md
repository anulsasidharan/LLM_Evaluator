# API Specification

Base path: `/api/v1/`

All responses use the envelope `{ "data": ..., "error": null }` (camelCase JSON).

| Method | Path | Status | Purpose |
|--------|------|--------|---------|
| GET | `/health` | 200 | Liveness |
| POST | `/models/analyze` | 202 | Queue a model analysis job |
| GET | `/results/{jobId}` | 200 / 404 | Poll job status and report |
| GET | `/models/search?q=` | 200 | Search models by name or tag |
| POST | `/comparisons` | 201 | Create a multi-model comparison |

Request and response bodies match the Pydantic schemas in `backend/app/models/schemas.py` and the examples in `CLAUDE.md` section 6.
