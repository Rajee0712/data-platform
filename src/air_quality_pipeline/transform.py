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
    hourly = raw.hourly
    timestamps = hourly.get("time", [])

    for i, ts in enumerate(timestamps):
        try:
            dt = datetime.fromisoformat(ts)
            record = AirQualityRecord(
                city=coords.city,
                timestamp=dt,
                date=dt.date(),
                pm2_5=hourly.get("pm2_5", [None])[i],
                pm10=hourly.get("pm10", [None])[i],
                carbon_monoxide=hourly.get("carbon_monoxide", [None])[i],
                nitrogen_dioxide=hourly.get("nitrogen_dioxide", [None])[i],
                ozone=hourly.get("ozone", [None])[i],
            )
            records.append(record)
        except Exception as e:
            logger.warning(f"Skipping record {i} for {coords.city}: {e}")

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
