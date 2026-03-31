"""Main pipeline orchestrator: Extract → Transform → Load."""

from loguru import logger

from weather_pipeline.config import settings
from weather_pipeline.extract import extract_all
from weather_pipeline.load import load
from weather_pipeline.transform import transform_all


def main() -> None:
    logger.info("Starting weather pipeline")
    logger.info(f"Cities: {settings.cities_list}")

    extracted = extract_all(settings.cities_list)
    records = transform_all(extracted)
    count = load(records)

    logger.info(f"Pipeline complete — {count} records loaded")
