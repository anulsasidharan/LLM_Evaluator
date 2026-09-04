# /project:review

Review code changes in the current branch for the LLM Evaluator project.

Checklist:
- [ ] Type hints present on all Python function signatures
- [ ] Pydantic schemas used for API request/response validation
- [ ] External API calls have timeouts and error handling
- [ ] No hardcoded API keys or secrets
- [ ] Tests added or updated for changed functionality
- [ ] Async patterns used correctly (no blocking I/O in async functions)
- [ ] Cache keys follow the project conventions (see data-pipeline rule)
- [ ] LLM tool functions are idempotent
- [ ] Frontend components use interfaces, not type aliases

Flag issues as:
- 🔴 **Critical**: Must fix before merge
- 🟡 **Suggestion**: Should improve
- 🟢 **Nice to have**: Optional polish
