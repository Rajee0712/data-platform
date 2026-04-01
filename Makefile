.PHONY: install lint format test run clean

install:
	uv sync --dev
	uv run pre-commit install

lint:
	uv run ruff check .

format:
	uv run ruff format .

fix:
	uv run ruff check --fix .
	uv run ruff format .

test:
	uv run pytest

run_weather:
	uv run python -m weather_pipeline 2>&1

run_air_quality:
	uv run python -m air_quality_pipeline 2>&1

run_all:
	uv run python -m weather_pipeline 2>&1
	uv run python -m air_quality_pipeline 2>&1

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	rm -f .coverage
	rm -f data/*.duckdb
