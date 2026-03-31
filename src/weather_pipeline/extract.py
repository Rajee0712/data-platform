"""Extract layer: fetch raw weather data from Open-Meteo API."""

import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from weather_pipeline.config import settings
from weather_pipeline.models import CityCoordinates, RawWeatherResponse

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"

HOURLY_VARIABLES = [
    "temperature_2m",
    "relative_humidity_2m",
    "wind_speed_10m",
    "precipitation",
]


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_coordinates(city: str, client: httpx.Client) -> CityCoordinates:
    """Resolve a city name to lat/lon via Open-Meteo geocoding API."""
    logger.debug(f"Resolving coordinates for {city}")
    response = client.get(
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
def fetch_weather(coords: CityCoordinates, client: httpx.Client) -> RawWeatherResponse:
    """Fetch hourly weather data for given coordinates."""
    logger.debug(
        f"Fetching weather for {coords.city} ({coords.latitude}, {coords.longitude})"
    )
    response = client.get(
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


def extract_city(
    city: str, client: httpx.Client
) -> tuple[CityCoordinates, RawWeatherResponse]:
    """Extract coordinates and weather data for a single city."""
    coords = fetch_coordinates(city, client)
    weather = fetch_weather(coords, client)
    logger.info(f"Extracted weather data for {city}")
    return coords, weather


def extract_all(cities: list[str]) -> list[tuple[CityCoordinates, RawWeatherResponse]]:
    """Extract weather data for all cities using a single shared HTTP client."""
    results = []
    with httpx.Client(timeout=30.0) as client:
        for city in cities:
            try:
                results.append(extract_city(city, client))
            except Exception as e:
                logger.error(f"Failed to extract data for {city}: {e}")
    return results
