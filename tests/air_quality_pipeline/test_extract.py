"""Tests for air_quality_pipeline.extract module."""

import asyncio

import httpx
import pytest
from tenacity import RetryError

from air_quality_pipeline.extract import (
    batched,
    extract_all,
    extract_all_async,
    extract_city_async,
    fetch_air_quality_async,
    fetch_coordinates_async,
)
from air_quality_pipeline.models import CityCoordinates


def test_batched():
    """Test the batched utility function."""
    items = list(range(10))
    batches = list(batched(items, 3))
    assert len(batches) == 4
    assert batches[0] == [0, 1, 2]
    assert batches[1] == [3, 4, 5]
    assert batches[2] == [6, 7, 8]
    assert batches[3] == [9]


def test_fetch_coordinates_async(httpx_mock):
    """Test fetch_coordinates_async with mocked HTTP response."""
    httpx_mock.add_response(
        url="https://geocoding-api.open-meteo.com/v1/search?name=Helsinki&count=1&language=en&format=json",
        json={
            "results": [{"latitude": 60.1699, "longitude": 24.9384, "name": "Helsinki"}]
        },
    )

    async def run_test():
        async with httpx.AsyncClient() as client:
            coords = await fetch_coordinates_async("Helsinki", client)
            assert coords.city == "Helsinki"
            assert coords.latitude == 60.1699
            assert coords.longitude == 24.9384

    asyncio.run(run_test())


def test_fetch_coordinates_async_not_found(httpx_mock):
    httpx_mock.add_response(
        url="https://geocoding-api.open-meteo.com/v1/search?name=NonExistentCity&count=1&language=en&format=json",
        json={"results": []},
        is_reusable=True,
    )

    async def run_test():
        async with httpx.AsyncClient() as client:
            with pytest.raises(RetryError):
                await fetch_coordinates_async("NonExistentCity", client)

    asyncio.run(run_test())


def test_fetch_air_quality_async(httpx_mock):
    """Test fetch_air_quality_async with mocked HTTP response."""
    coords = CityCoordinates(city="Helsinki", latitude=60.1699, longitude=24.9384)

    httpx_mock.add_response(
        url="https://air-quality-api.open-meteo.com/v1/measurements?coordinates=60.1699%2C24.9384&radius=25000&limit=1000&sort=desc&order_by=datetime",
        json={
            "results": [
                {
                    "parameter": "pm25",
                    "value": 10.5,
                    "unit": "µg/m³",
                    "date": {"utc": "2024-01-01T12:00:00Z"},
                    "coordinates": {"latitude": 60.1699, "longitude": 24.9384},
                }
            ]
        },
    )

    async def run_test():
        async with httpx.AsyncClient() as client:
            response = await fetch_air_quality_async(coords, client)
            assert len(response.results) == 1
            assert response.results[0]["parameter"] == "pm25"
            assert response.results[0]["value"] == 10.5

    asyncio.run(run_test())


def test_extract_city_async_success(httpx_mock):
    """Test extract_city_async with successful extraction."""
    # Mock geocoding response
    httpx_mock.add_response(
        url="https://geocoding-api.open-meteo.com/v1/search?name=Helsinki&count=1&language=en&format=json",
        json={
            "results": [{"latitude": 60.1699, "longitude": 24.9384, "name": "Helsinki"}]
        },
    )

    # Mock air quality response
    httpx_mock.add_response(
        url="https://air-quality-api.open-meteo.com/v1/measurements?coordinates=60.1699%2C24.9384&radius=25000&limit=1000&sort=desc&order_by=datetime",
        json={
            "results": [
                {
                    "parameter": "pm25",
                    "value": 10.5,
                    "unit": "µg/m³",
                    "date": {"utc": "2024-01-01T12:00:00Z"},
                    "coordinates": {"latitude": 60.1699, "longitude": 24.9384},
                }
            ]
        },
    )

    async def run_test():
        async with httpx.AsyncClient() as client:
            semaphore = asyncio.Semaphore(1)
            result = await extract_city_async("Helsinki", client, semaphore)
            assert result is not None
            coords, air_quality = result
            assert coords.city == "Helsinki"
            assert len(air_quality.results) == 1

    asyncio.run(run_test())


def test_extract_city_async_failure(httpx_mock):
    httpx_mock.add_response(
        url="https://geocoding-api.open-meteo.com/v1/search?name=BadCity&count=1&language=en&format=json",
        json={"results": []},
        is_reusable=True,
    )

    async def run_test():
        async with httpx.AsyncClient() as client:
            semaphore = asyncio.Semaphore(1)
            result = await extract_city_async("BadCity", client, semaphore)
            assert result is None

    asyncio.run(run_test())


def test_extract_all_async(httpx_mock):
    """Test extract_all_async with multiple cities."""
    # Mock responses for both cities
    httpx_mock.add_response(
        url="https://geocoding-api.open-meteo.com/v1/search?name=Helsinki&count=1&language=en&format=json",
        json={
            "results": [{"latitude": 60.1699, "longitude": 24.9384, "name": "Helsinki"}]
        },
    )
    httpx_mock.add_response(
        url="https://air-quality-api.open-meteo.com/v1/measurements?coordinates=60.1699%2C24.9384&radius=25000&limit=1000&sort=desc&order_by=datetime",
        json={"results": []},
    )

    async def run_test():
        results = await extract_all_async(["Helsinki"], batch_size=1)
        assert len(results) == 1
        coords, air_quality = results[0]
        assert coords.city == "Helsinki"

    asyncio.run(run_test())


def test_extract_all(httpx_mock):
    """Test sync entrypoint extract_all."""
    httpx_mock.add_response(
        url="https://geocoding-api.open-meteo.com/v1/search?name=Helsinki&count=1&language=en&format=json",
        json={
            "results": [{"latitude": 60.1699, "longitude": 24.9384, "name": "Helsinki"}]
        },
    )
    httpx_mock.add_response(
        url="https://air-quality-api.open-meteo.com/v1/measurements?coordinates=60.1699%2C24.9384&radius=25000&limit=1000&sort=desc&order_by=datetime",
        json={"results": []},
    )
    results = extract_all(["Helsinki"])
    assert isinstance(results, list)
