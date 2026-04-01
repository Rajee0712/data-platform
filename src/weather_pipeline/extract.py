"""Extract layer: fetch raw weather data from Open-Meteo API."""

import asyncio

import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from shared.extract_utils import extract_all_generic
from shared.models import CityCoordinates
from weather_pipeline.config import settings
from weather_pipeline.models import RawWeatherResponse

HOURLY_VARIABLES = [
    "temperature_2m",
    "relative_humidity_2m",
    "wind_speed_10m",
    "precipitation",
]


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def fetch_weather_async(
    coords: CityCoordinates, client: httpx.AsyncClient
) -> RawWeatherResponse:
    """Fetch hourly weather data for given coordinates."""
    logger.debug(
        f"Fetching weather for {coords.city} ({coords.latitude}, {coords.longitude})"
    )
    response = await client.get(
        f"{settings.api_base_url}/forecast",
        params={
            "latitude": coords.latitude,
            "longitude": coords.longitude,
            "hourly": ",".join(HOURLY_VARIABLES),
            "forecast_days": 1,
            "timezone": "auto",
        },
    )
    response.raise_for_status()
    return RawWeatherResponse(**response.json())


async def extract_all_async(
    cities: list[str],
) -> list[tuple[CityCoordinates, RawWeatherResponse]]:
    """Extract weather data for all cities using shared utilities."""
    return await extract_all_generic(cities, fetch_weather_async)


def extract_all(cities: list[str]) -> list[tuple[CityCoordinates, RawWeatherResponse]]:
    """Sync entrypoint for the async extract."""
    return asyncio.run(extract_all_async(cities))
