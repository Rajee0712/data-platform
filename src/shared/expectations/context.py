"""Shared Great Expectations context and utilities."""

import json
from pathlib import Path

import great_expectations as gx
from great_expectations.data_context import AbstractDataContext
from loguru import logger


def get_ephemeral_context() -> AbstractDataContext:
    """Create a shared ephemeral GE context."""
    return gx.get_context(mode="ephemeral")


def save_validation_results(results, name: str) -> Path:
    """Save validation results to JSON and return the path."""
    Path("data/validation").mkdir(parents=True, exist_ok=True)
    results_path = Path(f"data/validation/{name}_results.json")
    with open(results_path, "w") as f:
        json.dump(results.to_json_dict(), f, indent=2, default=str)
    logger.info(f"Validation results saved to {results_path}")
    return results_path
