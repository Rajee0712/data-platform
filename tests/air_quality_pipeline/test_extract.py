"""Tests for air_quality_pipeline.extract module."""

import asyncio

import httpx
import pytest

from air_quality_pipeline.extract import (
    extract_all,
    extract_all_async,
    fetch_air_quality_async,
)
from shared.extract_utils import batched, extract_city_generic, fetch_coordinates_async
from shared.models import CityCoordinates

MOCK_GEOCODING_RESPONSE = {
    "results": [{"latitude": 60.1699, "longitude": 24.9384, "name": "Helsinki"}]
}

MOCK_AIR_QUALITY_RESPONSE = {
    "latitude": 60.1699,
    "longitude": 24.9384,
    "timezone": "Europe/Helsinki",
    "hourly_units": {"pm2_5": "μg/m³"},
    "hourly": {
        "time": ["2024-01-01T00:00", "2024-01-01T01:00"],
        "pm2_5": [6.3, 6.5],
        "pm10": [9.5, 9.2],
        "carbon_monoxide": [217.0, 215.0],
        "nitrogen_dioxide": [10.7, 10.4],
        "ozone": [42.0, 38.0],
    },
}

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search?name=Helsinki&count=1&language=en&format=json"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality?latitude=60.1699&longitude=24.9384&hourly=pm2_5%2Cpm10%2Ccarbon_monoxide%2Cnitrogen_dioxide%2Cozone&forecast_days=1&timezone=auto"


def test_batched():
    items = list(range(10))
    batches = list(batched(items, 3))
    assert len(batches) == 4
    assert batches[0] == [0, 1, 2]
    assert batches[3] == [9]


def test_fetch_coordinates_async(httpx_mock):
    httpx_mock.add_response(url=GEOCODING_URL, json=MOCK_GEOCODING_RESPONSE)

    async def run():
        async with httpx.AsyncClient() as client:
            coords = await fetch_coordinates_async("Helsinki", client)
            assert coords.city == "Helsinki"
            assert coords.latitude == 60.1699

    asyncio.run(run())


def test_fetch_coordinates_async_not_found(httpx_mock):
    httpx_mock.add_response(
        url="https://geocoding-api.open-meteo.com/v1/search?name=NonExistentCity&count=1&language=en&format=json",
        json={"results": []},
    )

    async def run():
        async with httpx.AsyncClient() as client:
            with pytest.raises(ValueError, match="City not found: NonExistentCity"):
                await fetch_coordinates_async("NonExistentCity", client)

    asyncio.run(run())


def test_fetch_air_quality_async(httpx_mock):
    coords = CityCoordinates(city="Helsinki", latitude=60.1699, longitude=24.9384)
    httpx_mock.add_response(url=AIR_QUALITY_URL, json=MOCK_AIR_QUALITY_RESPONSE)

    async def run():
        async with httpx.AsyncClient() as client:
            response = await fetch_air_quality_async(coords, client)
            assert response.timezone == "Europe/Helsinki"
            assert len(response.hourly["time"]) == 2

    asyncio.run(run())


def test_extract_city_generic_success(httpx_mock):
    httpx_mock.add_response(url=GEOCODING_URL, json=MOCK_GEOCODING_RESPONSE)
    httpx_mock.add_response(url=AIR_QUALITY_URL, json=MOCK_AIR_QUALITY_RESPONSE)

    async def run():
        async with httpx.AsyncClient() as client:
            semaphore = asyncio.Semaphore(1)
            result = await extract_city_generic(
                "Helsinki", client, semaphore, fetch_air_quality_async
            )
            assert result is not None
            coords, air_quality = result
            assert coords.city == "Helsinki"
            assert air_quality.timezone == "Europe/Helsinki"

    asyncio.run(run())


def test_extract_city_generic_failure(httpx_mock):
    httpx_mock.add_response(
        url="https://geocoding-api.open-meteo.com/v1/search?name=BadCity&count=1&language=en&format=json",
        json={"results": []},
        is_reusable=True,
    )

    async def run():
        async with httpx.AsyncClient() as client:
            semaphore = asyncio.Semaphore(1)
            result = await extract_city_generic(
                "BadCity", client, semaphore, fetch_air_quality_async
            )
            assert result is None

    asyncio.run(run())


@pytest.mark.httpx_mock(assert_all_requests_were_expected=False)
def test_extract_all_async(httpx_mock):
    httpx_mock.add_response(url=GEOCODING_URL, json=MOCK_GEOCODING_RESPONSE)
    httpx_mock.add_response(url=AIR_QUALITY_URL, json=MOCK_AIR_QUALITY_RESPONSE)

    async def run():
        results = await extract_all_async(["Helsinki"])
        assert len(results) == 1
        assert results[0][0].city == "Helsinki"

    asyncio.run(run())


def test_extract_all(httpx_mock):
    httpx_mock.add_response(url=GEOCODING_URL, json=MOCK_GEOCODING_RESPONSE)
    httpx_mock.add_response(url=AIR_QUALITY_URL, json=MOCK_AIR_QUALITY_RESPONSE)
    results = extract_all(["Helsinki"])
    assert isinstance(results, list)
    assert len(results) == 1
