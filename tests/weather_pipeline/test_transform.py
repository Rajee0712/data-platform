"""Unit tests for the transform layer."""

from datetime import datetime

from weather_pipeline.models import CityCoordinates, RawWeatherResponse
from weather_pipeline.transform import parse_hourly_records, transform_all

MOCK_COORDS = CityCoordinates(city="Helsinki", latitude=60.16952, longitude=24.93545)

MOCK_RAW = RawWeatherResponse(
    latitude=60.16952,
    longitude=24.93545,
    timezone="Europe/Helsinki",
    hourly_units={
        "temperature_2m": "°C",
        "relative_humidity_2m": "%",
        "wind_speed_10m": "km/h",
        "precipitation": "mm",
    },
    hourly={
        "time": ["2024-01-15T00:00", "2024-01-15T01:00"],
        "temperature_2m": [-3.2, -3.5],
        "relative_humidity_2m": [85.0, 86.0],
        "wind_speed_10m": [12.0, 11.5],
        "precipitation": [0.0, 0.1],
    },
)


def test_parse_hourly_records_count():
    records = parse_hourly_records(MOCK_COORDS, MOCK_RAW)
    assert len(records) == 2


def test_parse_hourly_records_fields():
    records = parse_hourly_records(MOCK_COORDS, MOCK_RAW)
    r = records[0]
    assert r.city == "Helsinki"
    assert r.temperature_c == -3.2
    assert r.humidity_pct == 85.0
    assert r.windspeed_kmh == 12.0
    assert r.precipitation_mm == 0.0
    assert isinstance(r.timestamp, datetime)
    assert r.date == r.timestamp.date()


def test_parse_hourly_records_empty():
    empty_raw = RawWeatherResponse(
        latitude=60.0,
        longitude=24.0,
        timezone="Europe/Helsinki",
        hourly_units={},
        hourly={
            "time": [],
            "temperature_2m": [],
            "relative_humidity_2m": [],
            "wind_speed_10m": [],
            "precipitation": [],
        },
    )
    records = parse_hourly_records(MOCK_COORDS, empty_raw)
    assert records == []


def test_parse_hourly_skips_bad_record():
    bad_raw = RawWeatherResponse(
        latitude=60.0,
        longitude=24.0,
        timezone="Europe/Helsinki",
        hourly_units={},
        hourly={
            "time": ["2024-01-15T00:00", "bad-timestamp"],
            "temperature_2m": [-3.2, -3.5],
            "relative_humidity_2m": [85.0, 86.0],
            "wind_speed_10m": [12.0, 11.5],
            "precipitation": [0.0, 0.1],
        },
    )
    records = parse_hourly_records(MOCK_COORDS, bad_raw)
    assert len(records) == 1  # bad record skipped, good one kept


def test_transform_all():
    results = [(MOCK_COORDS, MOCK_RAW)]
    records = transform_all(results)
    assert len(records) == 2
    assert all(r.city == "Helsinki" for r in records)


def test_transform_all_empty():
    assert transform_all([]) == []
