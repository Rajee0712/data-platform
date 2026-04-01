"""Extract layer: fetch raw air quality data from Open-Meteo API."""

import asyncio
from itertools import islice

import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from air_quality_pipeline.config import settings
from air_quality_pipeline.models import (
    AIR_QUALITY_VARIABLES,
    CityCoordinates,
    RawAirQualityResponse,
)

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
BATCH_SIZE = 10
MAX_CONCURRENT = 5


def batched(iterable, n):
    """Split a list into batches of size n."""
    it = iter(iterable)
    while batch := list(islice(it, n)):
        yield batch


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def fetch_coordinates_async(
    city: str, client: httpx.AsyncClient
) -> CityCoordinates:
    """Resolve a city name to lat/lon via Open-Meteo geocoding API."""
    logger.debug(f"Resolving coordinates for {city}")
    response = await client.get(
        GEOCODING_URL,
        params={"name": city, "count": 1, "language": "en", "format": "json"},
    )
    response.raise_for_status()
    data = response.json()
    if not data.get("results"):
        raise ValueError(f"City not found: {city}")
    result = data["results"][0]
    return CityCoordinates(
        city=city,
        latitude=result["latitude"],
        longitude=result["longitude"],
    )


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


async def extract_city_async(
    city: str,
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
) -> tuple[CityCoordinates, RawAirQualityResponse] | None:
    """Extract coordinates and air quality for a single city."""
    async with semaphore:
        try:
            coords = await fetch_coordinates_async(city, client)
            air_quality = await fetch_air_quality_async(coords, client)
            logger.info(f"Extracted air quality data for {city}")
            return coords, air_quality
        except Exception as e:
            logger.error(f"Failed to extract data for {city}: {e}")
            return None


async def extract_all_async(
    cities: list[str],
    batch_size: int = BATCH_SIZE,
) -> list[tuple[CityCoordinates, RawAirQualityResponse]]:
    """Extract air quality data for all cities in batches."""
    all_results = []
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    async with httpx.AsyncClient(timeout=30.0) as client:
        for batch in batched(cities, batch_size):
            logger.info(f"Processing batch of {len(batch)} cities")
            tasks = [extract_city_async(city, client, semaphore) for city in batch]
            results = await asyncio.gather(*tasks)
            all_results.extend([r for r in results if r is not None])
            await asyncio.sleep(1)

    return all_results


def extract_all(
    cities: list[str],
) -> list[tuple[CityCoordinates, RawAirQualityResponse]]:
    """Sync entrypoint for the async extract."""
    return asyncio.run(extract_all_async(cities))
