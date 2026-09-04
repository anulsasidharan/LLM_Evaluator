# Code Style Rules

## Python (Backend)
- Follow PEP 8 strictly
- Type hints required on all function signatures
- Use `async def` for I/O-bound functions
- Docstrings: Google style on all public functions
- Max line length: 100 characters
- Imports: stdlib → third-party → local, separated by blank lines
- Use `pathlib.Path` over `os.path`

## TypeScript (Frontend)
- Strict mode enabled (`"strict": true` in tsconfig)
- Use `interface` over `type` for object shapes
- Prefer named exports over default exports
- Use functional React components only
- Destructure props in function signature

## General
- No magic numbers — use named constants
- Prefer early returns over nested conditionals
- Error messages must be actionable and include context
- Log at key decision points (info) and failures (error)
