"""Tests for shared.extract_utils module."""

import asyncio

import httpx
import pytest
from pytest_httpx import HTTPXMock
from tenacity import RetryError

from shared.extract_utils import (
    BATCH_SIZE,
    GEOCODING_URL,
    MAX_CONCURRENT,
    batched,
    extract_all_generic,
    extract_city_generic,
    fetch_coordinates_async,
)
from shared.models import CityCoordinates

# Test data
MOCK_GEOCODING_RESPONSE = {
    "results": [{"latitude": 60.1699, "longitude": 24.9384, "name": "Helsinki"}]
}

MOCK_DATA_RESPONSE = {"test": "data", "value": 42}


class MockDataResponse:
    """Mock response for testing generic extraction."""

    def __init__(self, data: dict):
        self.data = data


async def mock_data_fetcher(
    coords: CityCoordinates, client: httpx.AsyncClient
) -> MockDataResponse:
    """Mock data fetcher for testing."""
    response = await client.get(
        f"https://api.test.com/data?lat={coords.latitude}&lon={coords.longitude}"
    )
    response.raise_for_status()
    return MockDataResponse(response.json())


def test_constants():
    """Test that constants are defined correctly."""
    assert GEOCODING_URL == "https://geocoding-api.open-meteo.com/v1/search"
    assert BATCH_SIZE == 10
    assert MAX_CONCURRENT == 5


def test_batched():
    """Test the batched utility function."""
    items = list(range(10))
    batches = list(batched(items, 3))

    assert len(batches) == 4
    assert batches[0] == [0, 1, 2]
    assert batches[1] == [3, 4, 5]
    assert batches[2] == [6, 7, 8]
    assert batches[3] == [9]


def test_batched_empty():
    """Test batched with empty input."""
    items = []
    batches = list(batched(items, 3))
    assert len(batches) == 0


def test_batched_exact_size():
    """Test batched when input is exact multiple of batch size."""
    items = list(range(6))
    batches = list(batched(items, 3))

    assert len(batches) == 2
    assert batches[0] == [0, 1, 2]
    assert batches[1] == [3, 4, 5]


def test_fetch_coordinates_async_success(httpx_mock: HTTPXMock):
    """Test successful coordinate fetching."""
    httpx_mock.add_response(
        url="https://geocoding-api.open-meteo.com/v1/search?name=Helsinki&count=1&language=en&format=json",
        json=MOCK_GEOCODING_RESPONSE,
    )

    async def run_test():
        async with httpx.AsyncClient() as client:
            coords = await fetch_coordinates_async("Helsinki", client)

            assert coords.city == "Helsinki"
            assert coords.latitude == 60.1699
            assert coords.longitude == 24.9384

    asyncio.run(run_test())


@pytest.mark.httpx_mock(assert_all_requests_were_expected=False)
def test_fetch_coordinates_async_not_found(httpx_mock: HTTPXMock):
    """Test coordinate fetching when city is not found."""
    httpx_mock.add_response(
        url="https://geocoding-api.open-meteo.com/v1/search?name=NonExistentCity&count=1&language=en&format=json",
        json={"results": []},
        is_reusable=True,
    )

    async def run_test():
        async with httpx.AsyncClient() as client:
            with pytest.raises(ValueError, match="City not found: NonExistentCity"):
                await fetch_coordinates_async("NonExistentCity", client)

    asyncio.run(run_test())


@pytest.mark.httpx_mock(assert_all_requests_were_expected=False)
def test_fetch_coordinates_async_http_error(httpx_mock: HTTPXMock):
    """Test coordinate fetching with HTTP error."""
    httpx_mock.add_response(
        url="https://geocoding-api.open-meteo.com/v1/search?name=ErrorCity&count=1&language=en&format=json",
        status_code=500,
        is_reusable=True,
    )

    async def run_test():
        async with httpx.AsyncClient() as client:
            with pytest.raises(RetryError):  # Will raise after retries
                await fetch_coordinates_async("ErrorCity", client)

    asyncio.run(run_test())


def test_extract_city_generic_success(httpx_mock: HTTPXMock):
    """Test successful generic city extraction."""
    # Mock geocoding response
    httpx_mock.add_response(
        url="https://geocoding-api.open-meteo.com/v1/search?name=Helsinki&count=1&language=en&format=json",
        json=MOCK_GEOCODING_RESPONSE,
    )

    # Mock data fetcher response
    httpx_mock.add_response(
        url="https://api.test.com/data?lat=60.1699&lon=24.9384",
        json=MOCK_DATA_RESPONSE,
    )

    async def run_test():
        async with httpx.AsyncClient() as client:
            semaphore = asyncio.Semaphore(1)
            result = await extract_city_generic(
                "Helsinki", client, semaphore, mock_data_fetcher
            )

            assert result is not None
            coords, data = result
            assert coords.city == "Helsinki"
            assert data.data == MOCK_DATA_RESPONSE

    asyncio.run(run_test())


@pytest.mark.httpx_mock(assert_all_requests_were_expected=False)
def test_extract_city_generic_coordinate_failure(httpx_mock: HTTPXMock):
    """Test generic city extraction with coordinate failure."""
    httpx_mock.add_response(
        url="https://geocoding-api.open-meteo.com/v1/search?name=BadCity&count=1&language=en&format=json",
        json={"results": []},
        is_reusable=True,
    )

    async def run_test():
        async with httpx.AsyncClient() as client:
            semaphore = asyncio.Semaphore(1)
            result = await extract_city_generic(
                "BadCity", client, semaphore, mock_data_fetcher
            )
            assert result is None

    asyncio.run(run_test())


@pytest.mark.httpx_mock(assert_all_requests_were_expected=False)
def test_extract_city_generic_data_failure(httpx_mock: HTTPXMock):
    """Test generic city extraction with data fetcher failure."""
    # Mock successful geocoding
    httpx_mock.add_response(
        url="https://geocoding-api.open-meteo.com/v1/search?name=Helsinki&count=1&language=en&format=json",
        json=MOCK_GEOCODING_RESPONSE,
    )

    # Mock data fetcher failure
    httpx_mock.add_response(
        url="https://api.test.com/data?lat=60.1699&lon=24.9384",
        status_code=500,
        is_reusable=True,
    )

    async def run_test():
        async with httpx.AsyncClient() as client:
            semaphore = asyncio.Semaphore(1)
            result = await extract_city_generic(
                "Helsinki", client, semaphore, mock_data_fetcher
            )
            assert result is None

    asyncio.run(run_test())


def test_extract_all_generic_success(httpx_mock: HTTPXMock):
    """Test successful generic extraction for multiple cities."""
    # Mock geocoding responses
    httpx_mock.add_response(
        url="https://geocoding-api.open-meteo.com/v1/search?name=Helsinki&count=1&language=en&format=json",
        json=MOCK_GEOCODING_RESPONSE,
    )
    httpx_mock.add_response(
        url="https://geocoding-api.open-meteo.com/v1/search?name=Tampere&count=1&language=en&format=json",
        json={
            "results": [{"latitude": 61.4991, "longitude": 23.7871, "name": "Tampere"}]
        },
    )

    # Mock data responses
    httpx_mock.add_response(
        url="https://api.test.com/data?lat=60.1699&lon=24.9384",
        json=MOCK_DATA_RESPONSE,
    )
    httpx_mock.add_response(
        url="https://api.test.com/data?lat=61.4991&lon=23.7871",
        json={"test": "data2", "value": 84},
    )

    async def run_test():
        results = await extract_all_generic(
            ["Helsinki", "Tampere"], mock_data_fetcher, batch_size=2
        )

        assert len(results) == 2
        assert results[0][0].city == "Helsinki"
        assert results[1][0].city == "Tampere"

    asyncio.run(run_test())


@pytest.mark.httpx_mock(assert_all_requests_were_expected=False)
def test_extract_all_generic_partial_failure(httpx_mock: HTTPXMock):
    """Test generic extraction with partial failures."""
    # Helsinki succeeds
    httpx_mock.add_response(
        url="https://geocoding-api.open-meteo.com/v1/search?name=Helsinki&count=1&language=en&format=json",
        json=MOCK_GEOCODING_RESPONSE,
    )
    httpx_mock.add_response(
        url="https://api.test.com/data?lat=60.1699&lon=24.9384",
        json=MOCK_DATA_RESPONSE,
    )

    # BadCity fails
    httpx_mock.add_response(
        url="https://geocoding-api.open-meteo.com/v1/search?name=BadCity&count=1&language=en&format=json",
        json={"results": []},
        is_reusable=True,
    )

    async def run_test():
        results = await extract_all_generic(
            ["Helsinki", "BadCity"], mock_data_fetcher, batch_size=2
        )

        # Only Helsinki should succeed
        assert len(results) == 1
        assert results[0][0].city == "Helsinki"

    asyncio.run(run_test())


def test_extract_all_generic_empty_cities():
    """Test generic extraction with empty city list."""

    async def run_test():
        results = await extract_all_generic([], mock_data_fetcher)
        assert len(results) == 0

    asyncio.run(run_test())


def test_extract_all_generic_custom_batch_size(httpx_mock: HTTPXMock):
    """Test generic extraction with custom batch size."""
    cities = ["City1", "City2", "City3"]

    # Mock all responses
    for i, city in enumerate(cities):
        httpx_mock.add_response(
            url=f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json",
            json={"results": [{"latitude": 60 + i, "longitude": 24 + i, "name": city}]},
        )
        httpx_mock.add_response(
            url=f"https://api.test.com/data?lat={60 + i}.0&lon={24 + i}.0",
            json={"city": city, "value": i},
        )

    async def run_test():
        results = await extract_all_generic(cities, mock_data_fetcher, batch_size=1)

        assert len(results) == 3
        for i, (coords, _) in enumerate(results):
            assert coords.city == f"City{i + 1}"

    asyncio.run(run_test())
