"""Tests for air_quality_pipeline.transform module."""

from datetime import UTC, date, datetime

from air_quality_pipeline.models import CityCoordinates, RawAirQualityResponse
from air_quality_pipeline.transform import parse_air_quality_records, transform_all


def test_parse_air_quality_records():
    """Test parsing a single city's air quality measurements."""
    coords = CityCoordinates(city="Helsinki", latitude=60.1699, longitude=24.9384)
    raw = RawAirQualityResponse(
        results=[
            {
                "parameter": "pm25",
                "value": 10.5,
                "unit": "µg/m³",
                "date": {"utc": "2024-01-01T12:00:00Z"},
                "coordinates": {"latitude": 60.1699, "longitude": 24.9384},
            },
            {
                "parameter": "pm10",
                "value": 20.0,
                "unit": "µg/m³",
                "date": {"utc": "2024-01-01T13:00:00Z"},
                "coordinates": {"latitude": 60.1699, "longitude": 24.9384},
            },
        ]
    )

    records = parse_air_quality_records(coords, raw)
    assert len(records) == 2

    # Check first record
    record1 = records[0]
    assert record1.city == "Helsinki"
    assert record1.parameter == "pm25"
    assert record1.value == 10.5
    assert record1.unit == "µg/m³"
    assert record1.timestamp == datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    assert record1.date == date(2024, 1, 1)
    assert record1.coordinates_latitude == 60.1699
    assert record1.coordinates_longitude == 24.9384

    # Check second record
    record2 = records[1]
    assert record2.city == "Helsinki"
    assert record2.parameter == "pm10"
    assert record2.value == 20.0
    assert record2.timestamp == datetime(2024, 1, 1, 13, 0, 0, tzinfo=UTC)


def test_parse_air_quality_records_empty():
    """Test parsing with no measurements."""
    coords = CityCoordinates(city="Helsinki", latitude=60.1699, longitude=24.9384)
    raw = RawAirQualityResponse(results=[])

    records = parse_air_quality_records(coords, raw)
    assert len(records) == 0


def test_parse_air_quality_records_invalid_measurement():
    """Test parsing with invalid measurement data."""
    coords = CityCoordinates(city="Helsinki", latitude=60.1699, longitude=24.9384)
    raw = RawAirQualityResponse(
        results=[
            {
                "parameter": "pm25",
                "value": 10.5,
                "unit": "µg/m³",
                "date": {"utc": "2024-01-01T12:00:00Z"},
                "coordinates": {"latitude": 60.1699, "longitude": 24.9384},
            },
            {
                # Missing required fields - should be skipped
                "parameter": "pm10",
            },
        ]
    )

    records = parse_air_quality_records(coords, raw)
    # Only the first valid record should be included
    assert len(records) == 1
    assert records[0].parameter == "pm25"


def test_transform_all():
    """Test transforming multiple cities' data."""
    coords1 = CityCoordinates(city="Helsinki", latitude=60.1699, longitude=24.9384)
    raw1 = RawAirQualityResponse(
        results=[
            {
                "parameter": "pm25",
                "value": 10.5,
                "unit": "µg/m³",
                "date": {"utc": "2024-01-01T12:00:00Z"},
                "coordinates": {"latitude": 60.1699, "longitude": 24.9384},
            }
        ]
    )

    coords2 = CityCoordinates(city="Tampere", latitude=61.4991, longitude=23.7871)
    raw2 = RawAirQualityResponse(
        results=[
            {
                "parameter": "pm10",
                "value": 15.0,
                "unit": "µg/m³",
                "date": {"utc": "2024-01-01T12:00:00Z"},
                "coordinates": {"latitude": 61.4991, "longitude": 23.7871},
            }
        ]
    )

    extracted = [(coords1, raw1), (coords2, raw2)]
    all_records = transform_all(extracted)

    assert len(all_records) == 2
    assert all_records[0].city == "Helsinki"
    assert all_records[0].parameter == "pm25"
    assert all_records[1].city == "Tampere"
    assert all_records[1].parameter == "pm10"


def test_transform_all_empty():
    """Test transforming with no extracted data."""
    all_records = transform_all([])
    assert len(all_records) == 0
