"""Tests for air_quality_pipeline.models module."""

from datetime import UTC, date, datetime

from air_quality_pipeline.models import (
    AirQualityRecord,
    CityCoordinates,
    RawAirQualityResponse,
)


def test_city_coordinates():
    """Test CityCoordinates model."""
    coords = CityCoordinates(city="Helsinki", latitude=60.1699, longitude=24.9384)
    assert coords.city == "Helsinki"
    assert coords.latitude == 60.1699
    assert coords.longitude == 24.9384


def test_raw_air_quality_response():
    """Test RawAirQualityResponse model."""
    raw = RawAirQualityResponse(results=[{"parameter": "pm25", "value": 10.5}])
    assert len(raw.results) == 1
    assert raw.results[0]["parameter"] == "pm25"


def test_air_quality_record():
    """Test AirQualityRecord model with explicit datetime."""
    dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    record = AirQualityRecord(
        city="Helsinki",
        timestamp=dt,
        date=date(2024, 1, 1),
        parameter="pm25",
        value=10.5,
        unit="µg/m³",
        coordinates_latitude=60.1699,
        coordinates_longitude=24.9384,
    )

    assert record.city == "Helsinki"
    assert record.timestamp == dt
    assert record.date == date(2024, 1, 1)
    assert record.parameter == "pm25"
    assert record.value == 10.5
    assert record.unit == "µg/m³"
    assert record.coordinates_latitude == 60.1699
    assert record.coordinates_longitude == 24.9384
    # ingested_at should be auto-populated
    assert record.ingested_at is not None


def test_air_quality_record_ingested_at_auto():
    """Test that ingested_at is automatically set to current time."""
    dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    record = AirQualityRecord(
        city="Helsinki",
        timestamp=dt,
        date=date(2024, 1, 1),
        parameter="pm25",
        value=10.5,
        unit="µg/m³",
        coordinates_latitude=60.1699,
        coordinates_longitude=24.9384,
    )

    # ingested_at should be recent (within the last minute)
    now = datetime.now(UTC)
    time_diff = (now - record.ingested_at).total_seconds()
    assert time_diff < 60  # Less than 1 minute ago
