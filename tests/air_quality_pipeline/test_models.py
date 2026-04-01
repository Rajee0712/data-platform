"""Tests for air_quality_pipeline.models module."""

from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from air_quality_pipeline.models import (
    AirQualityRecord,
    CityCoordinates,
    RawAirQualityResponse,
)

MOCK_RAW = RawAirQualityResponse(
    latitude=60.1699,
    longitude=24.9384,
    timezone="Europe/Helsinki",
    hourly_units={"pm2_5": "μg/m³", "pm10": "μg/m³"},
    hourly={
        "time": ["2024-01-01T00:00", "2024-01-01T01:00"],
        "pm2_5": [6.3, 6.5],
        "pm10": [9.5, 9.2],
        "carbon_monoxide": [217.0, 215.0],
        "nitrogen_dioxide": [10.7, 10.4],
        "ozone": [42.0, 38.0],
    },
)


def test_city_coordinates():
    coords = CityCoordinates(city="Helsinki", latitude=60.1699, longitude=24.9384)
    assert coords.city == "Helsinki"
    assert coords.latitude == 60.1699


def test_raw_air_quality_response():
    assert MOCK_RAW.timezone == "Europe/Helsinki"
    assert len(MOCK_RAW.hourly["time"]) == 2


def test_air_quality_record():
    dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    record = AirQualityRecord(
        city="Helsinki",
        timestamp=dt,
        date=date(2024, 1, 1),
        pm2_5=6.3,
        pm10=9.5,
        carbon_monoxide=217.0,
        nitrogen_dioxide=10.7,
        ozone=42.0,
    )
    assert record.city == "Helsinki"
    assert record.pm2_5 == 6.3
    assert isinstance(record.ingested_at, datetime)


def test_air_quality_record_missing_field():
    with pytest.raises(ValidationError):
        AirQualityRecord(city="Helsinki")
