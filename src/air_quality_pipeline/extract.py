"""Extract layer: fetch raw air quality data from Open-Meteo API."""

import asyncio

import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from air_quality_pipeline.config import settings
from air_quality_pipeline.models import AIR_QUALITY_VARIABLES, RawAirQualityResponse
from shared.extract_utils import extract_all_generic
from shared.models import CityCoordinates


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def fetch_air_quality_async(
    coords: CityCoordinates, client: httpx.AsyncClient
) -> RawAirQualityResponse:
    """Fetch hourly air quality data for given coordinates."""
    logger.debug(
        f"Fetching air quality for {coords.city} ({coords.latitude}, {coords.longitude})"
    )
    response = await client.get(
        f"{settings.api_base_url}/air-quality",
        params={
            "latitude": coords.latitude,
            "longitude": coords.longitude,
            "hourly": ",".join(AIR_QUALITY_VARIABLES),
            "forecast_days": 1,
            "timezone": "auto",
        },
    )
    response.raise_for_status()
    return RawAirQualityResponse(**response.json())


async def extract_all_async(
    cities: list[str],
) -> list[tuple[CityCoordinates, RawAirQualityResponse]]:
    """Extract air quality data for all cities using shared utilities."""
    return await extract_all_generic(cities, fetch_air_quality_async)


def extract_all(
    cities: list[str],
) -> list[tuple[CityCoordinates, RawAirQualityResponse]]:
    """Sync entrypoint for the async extract."""
    return asyncio.run(extract_all_async(cities))
