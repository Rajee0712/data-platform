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

run:
	uv run python -m weather_pipeline.pipeline

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	rm -f .coverage
	rm -f data/*.duckdb
