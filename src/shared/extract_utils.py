"""Shared extraction utilities for all pipelines."""

import asyncio
from collections.abc import Awaitable, Callable
from itertools import islice

import httpx
from loguru import logger
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from shared.models import CityCoordinates

# Shared constants
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
BATCH_SIZE = 10
MAX_CONCURRENT = 5


def batched(iterable, n):
    """Split a list into batches of size n."""
    it = iter(iterable)
    while batch := list(islice(it, n)):
        yield batch


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
)
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


async def extract_city_generic[T](
    city: str,
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    data_fetcher: Callable[[CityCoordinates, httpx.AsyncClient], Awaitable[T]],
) -> tuple[CityCoordinates, T] | None:
    """Generic city data extraction pattern."""
    async with semaphore:
        try:
            coords = await fetch_coordinates_async(city, client)
            data = await data_fetcher(coords, client)
            logger.info(f"Extracted data for {city}")
            return coords, data
        except Exception as e:
            logger.error(f"Failed to extract data for {city}: {e}")
            return None


async def extract_all_generic[T](
    cities: list[str],
    data_fetcher: Callable[[CityCoordinates, httpx.AsyncClient], Awaitable[T]],
    batch_size: int = BATCH_SIZE,
) -> list[tuple[CityCoordinates, T]]:
    """Generic multi-city extraction with batching and rate limiting."""
    all_results = []
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    async with httpx.AsyncClient(timeout=30.0) as client:
        for batch in batched(cities, batch_size):
            logger.info(f"Processing batch of {len(batch)} cities")
            tasks = [
                extract_city_generic(city, client, semaphore, data_fetcher)
                for city in batch
            ]
            results = await asyncio.gather(*tasks)
            all_results.extend([r for r in results if r is not None])
            # Only sleep if there are more batches
            if len(all_results) < len(cities):
                await asyncio.sleep(1)

    return all_results
