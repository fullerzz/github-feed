# Agent Guide for github-feed
This file is for coding agents working in this repository.
Follow these conventions unless a task explicitly requires otherwise.

## Project Overview
- Language: Python 3.12+
- Package manager and runner: `uv`
- API framework: FastAPI
- Database layer: SQLModel + SQLite (DuckDB is installed but not primary here)
- Main app entrypoint: `src/github_feed/main.py`
- Core orchestration layer: `src/github_feed/engine.py`
- GitHub API client: `src/github_feed/github_client.py`
- Tests: `tests/engine_test.py`

## Repository Layout
- `src/github_feed/main.py`: FastAPI app, middleware, and routes
- `src/github_feed/engine.py`: business logic and refresh/retrieval orchestration
- `src/github_feed/github_client.py`: sync/async GitHub API calls and caching
- `src/github_feed/lib/models.py`: Pydantic API/domain models
- `src/github_feed/lib/utils.py`: utility helpers
- `src/github_feed/sql/models.py`: SQLModel table schemas
- `src/github_feed/sql/client.py`: DB access methods
- `tests/`: pytest tests
- `justfile`: canonical project commands
- `pyproject.toml`: lint/type/test config

## Environment and Setup
- Required env var: `GITHUB_TOKEN`
- Optional env var: `DB_FILENAME` (default `data/stargazing.db`)
- Install dependencies (including dev): `uv sync`

## Build, Run, Lint, and Test Commands
Use these preferred commands for agent tasks.

### Run and Build
- Dev server (FastAPI): `just run-dev`
- Prod-style run (FastAPI): `just run-prod`
- Uvicorn directly: `just uvicorn`
- Build Docker image: `just build`
- Run with Docker Compose: `just run`
- Rebuild and run detached: `just rebuild`

### Lint and Format
- Lint and auto-fix: `just lint`
- Lint equivalent: `uv run ruff check --fix .`
- Format code: `just fmt`
- Format equivalent: `uv run ruff format`
- Lint + format together: `just ruff`

### Type Checking
- Run mypy via dmypy: `just mypy`
- Start dmypy manually (if needed): `uv run dmypy start`
- Direct mypy run (optional): `uv run mypy`

### Testing
- Run all tests: `uv run pytest`
- Run single test file: `uv run pytest tests/engine_test.py`
- Run one test function: `uv run pytest tests/engine_test.py::test_load_config`
- Run tests by expression: `uv run pytest -k load_config`
- Run verbose output: `uv run pytest -v`

Pytest defaults from `pyproject.toml`:
- `--import-mode=importlib`
- `--disable-socket` (tests should be network-free)
- `--asyncio-mode=auto`

## Architecture and Behavioral Expectations
- Keep API boundary validation in Pydantic models (`lib/models.py`).
- Keep database writes/queries in `sql/client.py`; avoid leaking SQL into route handlers.
- Keep orchestration in `engine.py`; route handlers should stay thin.
- Preserve sync and async behavior parity where both paths exist.
- Keep datetime handling timezone-aware in UTC for logic.
- Convert to display/local time only in presentation-oriented computed fields.
- Preserve existing caching strategy in `github_client.py` unless task requires change.
- Handle partial failures in fan-out operations without crashing whole workflows.
- Favor additive, minimal changes over broad refactors.

## Code Style and Conventions

### Formatting and Lint Rules
- Ruff is the formatter and linter authority.
- Max line length: 110.
- Use 4-space indentation.
- Prefer double quotes unless escaping strongly favors single quotes.
- Keep trailing commas where formatter uses them.
- Do not manually fight formatter output.

### Imports
- Group imports: stdlib, third-party, local package.
- Let Ruff/isort maintain sorting and grouping.
- Prefer explicit imports over wildcard imports.
- Use aliases only for clarity or collision handling.

### Typing and Type Safety
- Add explicit type hints for parameters and return values.
- Prefer modern unions (`X | None`) over `Optional[X]`.
- Use precise `collections.abc` types where appropriate.
- Keep Pyright strict-mode expectations in mind.
- Mypy is strict; fix type issues instead of silencing by default.
- Use targeted type ignores only when unavoidable, with rationale.

### Naming
- `snake_case`: functions, variables, modules.
- `PascalCase`: classes and model types.
- `UPPER_SNAKE_CASE`: constants.
- Prefix private/internal helpers with `_`.
- Prefer descriptive names over abbreviations.

### Data Models
- Validate external payloads at boundaries with Pydantic models.
- Keep SQLModel schemas typed and aligned with domain models.
- Use computed fields/properties for stable derived values.
- Preserve current model shapes unless migration is part of task.

### Async and Concurrency
- Use async APIs for network-bound fan-out.
- Use `asyncio.gather(..., return_exceptions=True)` when partial success is acceptable.
- Handle per-task exceptions with context-rich logging.
- Keep ordering/sorting behavior deterministic in returned collections.

### Error Handling and Logging
- Catch specific exceptions first (`ValidationError`, `IntegrityError`, etc.).
- Use broad `except Exception` only as containment with logging.
- Include context in log messages (repo, URL, status, window).
- Avoid silent failures; log, re-raise, or return explicit failure state.
- Preserve existing logging style (`logger.info/warning/error/debug`).

### Testing Guidelines
- Use pytest with focused assertions.
- Prefer `pytest.mark.parametrize` for matrix-like inputs.
- Use fixtures like `monkeypatch` for environment/process isolation.
- Keep tests deterministic and offline by default.
- Add or adjust tests when changing config loading, mapping, or orchestration logic.

## Agent Execution Checklist
- Read `pyproject.toml` and `justfile` before introducing new commands.
- Keep changes minimal, scoped, and architecture-aligned.
- Run relevant checks before finalizing:
  - `just ruff`
  - `just mypy` for typing-heavy edits
  - `uv run pytest` or targeted pytest command
- Prefer fixing root causes over adding ignores/workarounds.
- Never commit secrets or hard-code tokens.

## Cursor and Copilot Rules
No rule files were found at the time of writing:
- `.cursor/rules/**`
- `.cursorrules`
- `.github/copilot-instructions.md`
If any of these files are added later, treat them as higher-priority repo instructions and update this guide.
