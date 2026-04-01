"""Transform layer: convert raw API responses into clean WeatherRecord models."""

from datetime import datetime

from loguru import logger

from shared.models import CityCoordinates
from weather_pipeline.models import RawWeatherResponse, WeatherRecord


def parse_hourly_records(
    coords: CityCoordinates,
    raw: RawWeatherResponse,
) -> list[WeatherRecord]:
    """Convert a raw API response into a list of typed WeatherRecord rows."""
    records = []
    hourly = raw.hourly

    timestamps = hourly.get("time", [])
    temperatures = hourly.get("temperature_2m", [])
    humidities = hourly.get("relative_humidity_2m", [])
    windspeeds = hourly.get("wind_speed_10m", [])
    precipitations = hourly.get("precipitation", [])

    for i, ts in enumerate(timestamps):
        try:
            dt = datetime.fromisoformat(ts)
            record = WeatherRecord(
                city=coords.city,
                timestamp=dt,
                date=dt.date(),
                temperature_c=temperatures[i],
                humidity_pct=humidities[i],
                windspeed_kmh=windspeeds[i],
                precipitation_mm=precipitations[i],
            )
            records.append(record)
        except Exception as e:
            logger.warning(f"Skipping record {i} for {coords.city}: {e}")

    logger.info(f"Transformed {len(records)} records for {coords.city}")
    return records


def transform_all(
    extracted: list[tuple[CityCoordinates, RawWeatherResponse]],
) -> list[WeatherRecord]:
    """Transform all extracted city data into a flat list of WeatherRecords."""
    all_records = []
    for coords, raw in extracted:
        records = parse_hourly_records(coords, raw)
        all_records.extend(records)
    logger.info(f"Total records transformed: {len(all_records)}")
    return all_records
