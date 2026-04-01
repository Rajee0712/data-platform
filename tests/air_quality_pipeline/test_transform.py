"""Tests for air_quality_pipeline.transform module."""

from datetime import datetime

from air_quality_pipeline.models import RawAirQualityResponse
from air_quality_pipeline.transform import parse_air_quality_records, transform_all
from shared.models import CityCoordinates

MOCK_COORDS = CityCoordinates(city="Helsinki", latitude=60.1699, longitude=24.9384)

MOCK_RAW = RawAirQualityResponse(
    latitude=60.1699,
    longitude=24.9384,
    timezone="Europe/Helsinki",
    hourly_units={"pm2_5": "μg/m³"},
    hourly={
        "time": ["2024-01-01T00:00", "2024-01-01T01:00"],
        "pm2_5": [6.3, 6.5],
        "pm10": [9.5, 9.2],
        "carbon_monoxide": [217.0, 215.0],
        "nitrogen_dioxide": [10.7, 10.4],
        "ozone": [42.0, 38.0],
    },
)


def test_parse_air_quality_records_count():
    records = parse_air_quality_records(MOCK_COORDS, MOCK_RAW)
    assert len(records) == 2


def test_parse_air_quality_records_fields():
    records = parse_air_quality_records(MOCK_COORDS, MOCK_RAW)
    r = records[0]
    assert r.city == "Helsinki"
    assert r.pm2_5 == 6.3
    assert r.pm10 == 9.5
    assert r.carbon_monoxide == 217.0
    assert r.nitrogen_dioxide == 10.7
    assert r.ozone == 42.0
    assert isinstance(r.timestamp, datetime)
    assert r.date == r.timestamp.date()


def test_parse_air_quality_records_empty():
    empty_raw = RawAirQualityResponse(
        latitude=60.0,
        longitude=24.0,
        timezone="Europe/Helsinki",
        hourly_units={},
        hourly={
            "time": [],
            "pm2_5": [],
            "pm10": [],
            "carbon_monoxide": [],
            "nitrogen_dioxide": [],
            "ozone": [],
        },
    )
    records = parse_air_quality_records(MOCK_COORDS, empty_raw)
    assert records == []


def test_parse_air_quality_skips_bad_record():
    bad_raw = RawAirQualityResponse(
        latitude=60.0,
        longitude=24.0,
        timezone="Europe/Helsinki",
        hourly_units={},
        hourly={
            "time": ["2024-01-01T00:00", "bad-timestamp"],
            "pm2_5": [6.3, 6.5],
            "pm10": [9.5, 9.2],
            "carbon_monoxide": [217.0, 215.0],
            "nitrogen_dioxide": [10.7, 10.4],
            "ozone": [42.0, 38.0],
        },
    )
    records = parse_air_quality_records(MOCK_COORDS, bad_raw)
    assert len(records) == 1


def test_transform_all():
    results = [(MOCK_COORDS, MOCK_RAW)]
    records = transform_all(results)
    assert len(records) == 2
    assert all(r.city == "Helsinki" for r in records)


def test_transform_all_empty():
    assert transform_all([]) == []
