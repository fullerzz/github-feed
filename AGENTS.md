# Agent Guide for github-feed
This file is for coding agents working in this repository.
Follow these conventions unless a task explicitly requires otherwise.

## Project Snapshot
- Language: Python 3.12+
- Package manager and runner: `uv`
- API framework: FastAPI
- Terminal UI framework: Textual
- Database layer: SQLModel + SQLite
- Main API entrypoint: `src/github_feed/main.py`
- Main orchestration layer: `src/github_feed/engine.py`
- GitHub API client: `src/github_feed/github_client.py`
- Database access layer: `src/github_feed/sql/client.py`
- Tests: `tests/engine_test.py`

## Repository Layout
- `src/github_feed/main.py`: FastAPI app setup, middleware, and routes
- `src/github_feed/engine.py`: orchestration for refresh and retrieval flows
- `src/github_feed/github_client.py`: sync and async GitHub API access + caching
- `src/github_feed/lib/models.py`: Pydantic API/domain models
- `src/github_feed/lib/utils.py`: utility helpers
- `src/github_feed/sql/models.py`: SQLModel table schemas
- `src/github_feed/sql/client.py`: SQLModel session-based DB methods
- `src/github_feed/tui/app.py`: Textual TUI application
- `tests/`: pytest test suite
- `justfile`: canonical dev commands
- `pyproject.toml`: lint, type, and pytest config

## Environment and Setup
- Required env var: `GITHUB_TOKEN`
- Optional env vars:
  - `DB_FILENAME` (default: `data/stargazing.db`)
  - `RELEASE_WINDOW_DAYS` (used by TUI recent mode, default 30)
- Install dependencies (including dev): `uv sync`

## Build, Run, Lint, and Test Commands
Use these as the default commands for agent tasks.

### Run the Application
- API dev server: `just run-dev`
- API prod-style run: `just run-prod`
- Uvicorn direct: `just uvicorn`
- TUI app: `just run-tui`

### Docker
- Build image: `just build`
- Run compose stack: `just run`
- Rebuild and run detached: `just rebuild`

### Lint and Format
- Lint (with auto-fixes): `just lint`
- Format: `just fmt`
- Lint + format: `just ruff`
- Ruff equivalents:
  - `uv run ruff check --fix .`
  - `uv run ruff format`

### Type Checking
- Preferred type check: `just mypy`
- dmypy direct: `uv run dmypy check src/github_feed`
- Full mypy run (optional): `uv run mypy`

### Testing (Pytest)
- Run all tests: `uv run pytest`
- Run a single test file: `uv run pytest tests/engine_test.py`
- Run a single test function: `uv run pytest tests/engine_test.py::test_load_config`
- Run tests matching a pattern: `uv run pytest -k load_config`
- Verbose test output: `uv run pytest -v`

Pytest defaults from `pyproject.toml`:
- `--import-mode=importlib`
- `--disable-socket` (tests must be network-free by default)
- `--asyncio-mode=auto`

## Architecture and Behavior Expectations
- Keep route handlers thin; orchestration belongs in `engine.py`.
- Keep SQL logic in `sql/client.py`; avoid query logic in routes.
- Keep API payload validation in Pydantic models (`lib/models.py`).
- Preserve sync/async behavior parity where both paths exist.
- Preserve caching behavior in `github_client.py` unless task requires change.
- Keep results deterministic (sort releases by `created_at` descending where applicable).
- Use timezone-aware UTC datetimes for logic and persistence.
- Convert to local display time only in presentation-focused computed fields.
- Handle fan-out partial failures without collapsing the whole workflow.

## Code Style and Conventions

### Formatting and Linting
- Ruff is the formatting and linting authority.
- Max line length: 110.
- Use 4-space indentation.
- Prefer double quotes unless escaping strongly favors single quotes.
- Keep trailing commas where formatter expects them.
- Do not hand-format against Ruff output.

### Imports
- Group imports as: stdlib, third-party, local package.
- Keep imports sorted via Ruff/isort.
- Prefer explicit imports over wildcard imports.
- Alias imports only for clarity or name collision handling.

### Typing
- Add explicit type hints for function params and return types.
- Prefer modern unions (`X | None`) over `Optional[X]`.
- Prefer `collections.abc` types for interfaces (`Sequence`, `Mapping`, etc.).
- Mypy is strict (`[tool.mypy] strict = true`): fix root type issues.
- Pyright strict mode is configured; avoid introducing unknown-type regressions.
- Use `type: ignore` only when unavoidable, narrowly scoped, and justified.

### Naming
- `snake_case`: functions, methods, variables, modules
- `PascalCase`: classes and model types
- `UPPER_SNAKE_CASE`: constants
- Prefix internal helpers with `_` when not part of public API
- Prefer descriptive names over abbreviations

### Models and Data Mapping
- Validate external API payloads with Pydantic models.
- Keep SQLModel schemas aligned with domain model intent.
- Keep field names stable unless migration/refactor is explicit.
- Use computed fields for deterministic derived presentation values.

### Async and Concurrency
- Use async flows for network-bound fan-out work.
- Prefer `asyncio.gather(..., return_exceptions=True)` when partial success is acceptable.
- Handle per-task exceptions with contextual logging.
- Avoid introducing non-deterministic ordering in returned collections.

### Error Handling and Logging
- Catch specific exceptions first (`ValidationError`, `IntegrityError`, `NoResultFound`, etc.).
- Use broad `except Exception` only as containment with logging context.
- Include useful context in logs (repo name, URL, status, time window).
- Avoid silent failures; log and return explicit behavior.
- Follow existing logger style: `logger.info`, `logger.warning`, `logger.error`, `logger.debug`.

### Testing Expectations
- Use pytest with deterministic, focused assertions.
- Prefer `pytest.mark.parametrize` for matrix-style inputs.
- Use `monkeypatch` and stubs for environment and behavior isolation.
- Keep tests offline and deterministic (`--disable-socket`).
- Add/adjust tests when changing orchestration, config loading, or mapping logic.

## Agent Workflow Checklist
- Read `pyproject.toml` and `justfile` before introducing new tooling.
- Keep changes minimal, scoped, and architecture-aligned.
- Run relevant checks before finalizing:
  - `just ruff`
  - `just mypy` for typing-heavy edits
  - `uv run pytest` or a targeted pytest command
- Prefer fixing root causes over adding ignores/workarounds.
- Do not commit secrets or hard-code tokens.

## Cursor and Copilot Rules
No repository-specific Cursor or Copilot rule files were found:
- `.cursor/rules/**`
- `.cursorrules`
- `.github/copilot-instructions.md`

If any of these files are added later, treat them as higher-priority instructions than this guide and update this file.
