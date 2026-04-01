"""Transform layer: convert raw API responses into clean AirQualityRecord models."""

from datetime import datetime

from loguru import logger

from air_quality_pipeline.models import (
    AirQualityRecord,
    CityCoordinates,
    RawAirQualityResponse,
)


def parse_air_quality_records(
    coords: CityCoordinates,
    raw: RawAirQualityResponse,
) -> list[AirQualityRecord]:
    """Convert a raw API response into a list of typed AirQualityRecord rows."""
    records = []

    for measurement in raw.results:
        try:
            dt = datetime.fromisoformat(
                measurement["date"]["utc"].replace("Z", "+00:00")
            )
            record = AirQualityRecord(
                city=coords.city,
                timestamp=dt,
                date=dt.date(),
                parameter=measurement["parameter"],
                value=measurement["value"],
                unit=measurement["unit"],
                coordinates_latitude=measurement["coordinates"]["latitude"],
                coordinates_longitude=measurement["coordinates"]["longitude"],
            )
            records.append(record)
        except Exception as e:
            logger.warning(f"Skipping measurement for {coords.city}: {e}")

    logger.info(f"Transformed {len(records)} records for {coords.city}")
    return records


def transform_all(
    extracted: list[tuple[CityCoordinates, RawAirQualityResponse]],
) -> list[AirQualityRecord]:
    """Transform all extracted city data into a flat list of AirQualityRecords."""
    all_records = []
    for coords, raw in extracted:
        records = parse_air_quality_records(coords, raw)
        all_records.extend(records)
    logger.info(f"Total records transformed: {len(all_records)}")
    return all_records
