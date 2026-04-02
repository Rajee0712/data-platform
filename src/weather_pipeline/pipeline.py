"""Main pipeline orchestrator: Extract → Transform → Load → Validate."""

from loguru import logger

from weather_pipeline.config import settings
from weather_pipeline.extract import extract_all
from weather_pipeline.load import get_connection, load
from weather_pipeline.transform import transform_all
from weather_pipeline.validate import validate_weather_data


def main() -> None:
    logger.info("Starting weather pipeline")
    logger.info(f"Cities: {settings.cities_list}")

    extracted = extract_all(settings.cities_list)
    records = transform_all(extracted)
    count = load(records)

    logger.info(f"Pipeline complete — {count} records loaded")

    with get_connection(settings.db_path) as conn:
        validate_weather_data(conn)
