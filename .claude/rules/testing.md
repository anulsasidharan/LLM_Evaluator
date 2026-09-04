# Testing Rules

## Python Tests
- Use `pytest` as the test runner
- Place tests in `backend/tests/` mirroring `backend/app/` structure
- Name test files `test_<module>.py`
- Name test functions `test_<behavior>_<scenario>`
- Use `pytest-asyncio` for async tests
- Mock external APIs (HuggingFace, Ollama, LLM providers) — never call live services in tests
- Use `pytest-httpx` or `respx` for HTTP mocking

## Frontend Tests
- Use Vitest + React Testing Library
- Test user interactions, not implementation details
- Place tests next to components: `Component.test.tsx`

## Coverage
- Target 80% coverage for services and API routes
- Unit tests for data normalization and resource calculation logic
- Integration tests for LLM tool execution flows
- E2E tests for the full analyze → report pipeline
