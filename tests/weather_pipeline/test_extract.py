"""Unit tests for the extract layer."""

import httpx
import pytest
from pytest_httpx import HTTPXMock
from tenacity import RetryError

from weather_pipeline.extract import (
    extract_all,
    extract_city,
    fetch_coordinates,
    fetch_weather,
)
from weather_pipeline.models import CityCoordinates

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


def test_fetch_coordinates(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json=MOCK_GEOCODING_RESPONSE)
    with httpx.Client() as client:
        coords = fetch_coordinates("Helsinki", client)
    assert coords.city == "Helsinki"
    assert coords.latitude == 60.16952
    assert coords.longitude == 24.93545


def test_fetch_coordinates_city_not_found(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json={"results": []}, is_reusable=True)
    with httpx.Client() as client, pytest.raises(RetryError):
        fetch_coordinates("FakeCity", client)


def test_fetch_weather(httpx_mock: HTTPXMock):
    coords = CityCoordinates(city="Helsinki", latitude=60.16952, longitude=24.93545)
    httpx_mock.add_response(json=MOCK_WEATHER_RESPONSE)
    with httpx.Client() as client:
        weather = fetch_weather(coords, client)
    assert weather.timezone == "Europe/Helsinki"
    assert len(weather.hourly["temperature_2m"]) == 2


def test_extract_city(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json=MOCK_GEOCODING_RESPONSE)
    httpx_mock.add_response(json=MOCK_WEATHER_RESPONSE)
    with httpx.Client() as client:
        coords, weather = extract_city("Helsinki", client)
    assert coords.city == "Helsinki"
    assert weather.timezone == "Europe/Helsinki"


def test_extract_all_success(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json=MOCK_GEOCODING_RESPONSE)
    httpx_mock.add_response(json=MOCK_WEATHER_RESPONSE)
    results = extract_all(["Helsinki"])
    assert len(results) == 1
    coords, weather = results[0]
    assert coords.city == "Helsinki"


def test_extract_all_skips_failed_city(httpx_mock: HTTPXMock):
    """A bad city should be skipped, not crash the whole pipeline."""
    httpx_mock.add_response(json={"results": []}, is_reusable=True)
    results = extract_all(["FakeCity"])
    assert results == []  # failed city skipped, no crash


def test_extract_all_partial_failure(httpx_mock: HTTPXMock):
    """Good cities still extracted even if one fails."""
    # FakeCity geocoding fails — 3 retry attempts
    httpx_mock.add_response(json={"results": []})
    httpx_mock.add_response(json={"results": []})
    httpx_mock.add_response(json={"results": []})
    # Helsinki succeeds
    httpx_mock.add_response(json=MOCK_GEOCODING_RESPONSE)
    httpx_mock.add_response(json=MOCK_WEATHER_RESPONSE)

    results = extract_all(["FakeCity", "Helsinki"])
    assert len(results) == 1
    assert results[0][0].city == "Helsinki"
