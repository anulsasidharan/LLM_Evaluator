# API Conventions

## REST Endpoints
- Base path: `/api/v1/`
- Use plural nouns for resources: `/models`, `/comparisons`, `/results`
- POST for actions that create or trigger work, GET for retrieval
- Return consistent envelope: `{ "data": ..., "error": null }` or `{ "data": null, "error": { "code": "...", "message": "..." } }`
- Use HTTP status codes correctly: 200 OK, 201 Created, 202 Accepted (async jobs), 400/422 validation, 404 not found, 500 server error

## Async Jobs
- Long-running analyses return 202 with a `jobId`
- Poll via `GET /api/v1/results/{jobId}`
- Job statuses: `queued`, `processing`, `completed`, `failed`

## Validation
- Use Pydantic models for all request/response schemas
- Validate at the API boundary, not deep in services
- Return structured validation errors with field paths

## Naming
- camelCase for JSON fields
- snake_case for Python variables and DB columns
- PascalCase for Pydantic models and TypeScript interfaces
