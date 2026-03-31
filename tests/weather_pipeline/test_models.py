"""
Unit tests for the data models in weather_pipeline.models.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from weather_pipeline.models import CityCoordinates, RawWeatherResponse, WeatherRecord


def test_weather_record_valid():
    record = WeatherRecord(
        city="Helsinki",
        timestamp=datetime(2024, 1, 15, 12, 0),
        date=datetime(2024, 1, 15).date(),
        temperature_c=-5.2,
        humidity_pct=78.0,
        windspeed_kmh=12.5,
        precipitation_mm=0.0,
    )
    assert record.city == "Helsinki"
    assert record.temperature_c == -5.2
    assert isinstance(record.ingested_at, datetime)  # auto-set


def test_weather_record_missing_field():
    with pytest.raises(ValidationError):
        WeatherRecord(city="Helsinki")  # missing required fields


def test_city_coordinates_valid():
    coord = CityCoordinates(city="Pori", latitude=61.48, longitude=21.79)
    assert coord.latitude == 61.48


def test_raw_weather_response_valid():
    raw = RawWeatherResponse(
        latitude=61.48,
        longitude=21.79,
        timezone="Europe/Helsinki",
        hourly_units={"temperature_2m": "°C"},
        hourly={"temperature_2m": [1.0, 2.0]},
    )
    assert raw.timezone == "Europe/Helsinki"
