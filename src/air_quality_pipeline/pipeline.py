"""Main pipeline orchestrator: Extract → Transform → Load."""

from loguru import logger

from air_quality_pipeline.config import settings
from air_quality_pipeline.extract import extract_all
from air_quality_pipeline.load import load
from air_quality_pipeline.transform import transform_all


def main() -> None:
    logger.info("Starting air quality pipeline")
    logger.info(f"Cities: {settings.cities_list}")

    extracted = extract_all(settings.cities_list)
    records = transform_all(extracted)
    count = load(records)

    logger.info(f"Pipeline complete — {count} records loaded")
