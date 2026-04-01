# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project Overview

A data platform monorepo that ingests data from multiple APIs and loads into DuckDB
for cross-source analysis. Defaults to Finnish cities but supports nordic, europe and
world scopes via `CITY_SCOPE` env var.

## Stack
- **Python 3.13**, **uv**, **pydantic v2**, **httpx** (async), **duckdb**, **loguru**
- **ruff** for linting/formatting, **pytest** for testing, **pytest-httpx** for HTTP mocking
- **pre-commit**, **GitHub Actions CI**, **Docker**

## Commands
```bash
make install    # setup deps + pre-commit hooks
make run        # run pipeline
make test       # pytest with coverage
make lint       # check only — fails if issues found
make format     # fix formatting
make fix        # auto-fix lint + format
make clean      # remove generated files
```

See `.claude/commands/` for reusable slash commands:
- `/new-pipeline` — scaffold a new pipeline
- `/add-test` — add missing tests to reach 100% coverage
- `/review` — review current diff for issues

## Architecture
Every pipeline follows the same ELT pattern:
```
extract.py    → async httpx + tenacity retries → RawModel
transform.py  → RawModel → list[Record]
load.py       → INSERT OR REPLACE into DuckDB
pipeline.py   → thin orchestrator E→T→L
config.py     → pydantic-settings singleton
models.py     → pydantic models only, never raw dicts
__main__.py   → entrypoint for python -m <pipeline>
```

## Key Conventions
- **Cities** — always import from `shared.cities`, never hardcode
- **Config** — import `settings` singleton, never instantiate `Settings()` in app code
- **Async boundary** — extract is async internally, `extract_all()` is sync via `asyncio.run()`
- **Idempotency** — `INSERT OR REPLACE` on `(city, timestamp)` — safe to rerun
- **Fault isolation** — one failed city never crashes the pipeline
- **Logging** — loguru only, never `print()`
- **Datetime** — always `datetime.now(UTC)`, never `utcnow()` or `now()`

## Testing Rules
- 100% coverage target
- Mock all HTTP with `pytest-httpx` — never hit real APIs
- Use `:memory:` DuckDB in load tests
- Async tests use `asyncio.run()` directly — no `pytest-asyncio`

## Git Workflow
- Branch from main: `feature/<name>`
- Never commit directly to main
- PR → squash merge → delete branch
- Commit format: `feat:` `fix:` `chore:` `docs:` `ci:` `test:`
