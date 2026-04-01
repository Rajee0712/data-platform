"""Unit tests for the extract layer."""

import asyncio

import httpx
import pytest
from pytest_httpx import HTTPXMock

from shared.extract_utils import extract_city_generic, fetch_coordinates_async
from shared.models import CityCoordinates
from weather_pipeline.extract import (
    extract_all,
    fetch_weather_async,
)

MOCK_GEOCODING_RESPONSE = {
    "results": [
        {
            "name": "Helsinki",
            "latitude": 60.16952,
            "longitude": 24.93545,
            "country": "Finland",
        }
    ]
}

MOCK_WEATHER_RESPONSE = {
    "latitude": 60.16952,
    "longitude": 24.93545,
    "timezone": "Europe/Helsinki",
    "hourly_units": {
        "temperature_2m": "°C",
        "relative_humidity_2m": "%",
        "wind_speed_10m": "km/h",
        "precipitation": "mm",
    },
    "hourly": {
        "time": ["2024-01-15T00:00", "2024-01-15T01:00"],
        "temperature_2m": [-3.2, -3.5],
        "relative_humidity_2m": [85.0, 86.0],
        "wind_speed_10m": [12.0, 11.5],
        "precipitation": [0.0, 0.1],
    },
}


@pytest.fixture
def semaphore():
    return asyncio.Semaphore(5)


def test_fetch_coordinates_async(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json=MOCK_GEOCODING_RESPONSE)

    async def run():
        async with httpx.AsyncClient() as client:
            return await fetch_coordinates_async("Helsinki", client)

    coords = asyncio.run(run())
    assert coords.city == "Helsinki"
    assert coords.latitude == 60.16952
    assert coords.longitude == 24.93545


def test_fetch_coordinates_city_not_found(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json={"results": []})

    async def run():
        async with httpx.AsyncClient() as client:
            return await fetch_coordinates_async("FakeCity", client)

    with pytest.raises(ValueError, match="City not found: FakeCity"):
        asyncio.run(run())


def test_fetch_weather_async(httpx_mock: HTTPXMock):
    coords = CityCoordinates(city="Helsinki", latitude=60.16952, longitude=24.93545)
    httpx_mock.add_response(json=MOCK_WEATHER_RESPONSE)

    async def run():
        async with httpx.AsyncClient() as client:
            return await fetch_weather_async(coords, client)

    weather = asyncio.run(run())
    assert weather.timezone == "Europe/Helsinki"
    assert len(weather.hourly["temperature_2m"]) == 2


def test_extract_city_generic_success(httpx_mock: HTTPXMock, semaphore):
    httpx_mock.add_response(json=MOCK_GEOCODING_RESPONSE)
    httpx_mock.add_response(json=MOCK_WEATHER_RESPONSE)

    async def run():
        async with httpx.AsyncClient() as client:
            return await extract_city_generic(
                "Helsinki", client, semaphore, fetch_weather_async
            )

    coords, weather = asyncio.run(run())
    assert coords.city == "Helsinki"
    assert weather.timezone == "Europe/Helsinki"


def test_extract_city_generic_failure(httpx_mock: HTTPXMock, semaphore):
    httpx_mock.add_response(json={"results": []}, is_reusable=True)

    async def run():
        async with httpx.AsyncClient() as client:
            return await extract_city_generic(
                "FakeCity", client, semaphore, fetch_weather_async
            )

    result = asyncio.run(run())
    assert result is None


def test_extract_all_success(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json=MOCK_GEOCODING_RESPONSE)
    httpx_mock.add_response(json=MOCK_WEATHER_RESPONSE)
    results = extract_all(["Helsinki"])
    assert len(results) == 1
    assert results[0][0].city == "Helsinki"


def test_extract_all_skips_failed_city(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json={"results": []}, is_reusable=True)
    results = extract_all(["FakeCity"])
    assert results == []


@pytest.mark.httpx_mock(assert_all_requests_were_expected=False)
def test_extract_all_partial_failure(httpx_mock: HTTPXMock):
    # FakeCity fails — no retries on ValueError
    httpx_mock.add_response(json={"results": []})
    # Helsinki succeeds
    httpx_mock.add_response(json=MOCK_GEOCODING_RESPONSE)
    httpx_mock.add_response(json=MOCK_WEATHER_RESPONSE)
    results = extract_all(["FakeCity", "Helsinki"])
    assert len(results) == 1
    assert results[0][0].city == "Helsinki"
