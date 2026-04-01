"""Tests for shared.models module."""

from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from shared.models import BaseRawResponse, BaseRecord, CityCoordinates


class SampleRawResponse(BaseRawResponse):
    """Test implementation of BaseRawResponse."""

    data: dict
    metadata: dict

    def get_data_field(self) -> str:
        return "data"


class SampleRecord(BaseRecord):
    """Test implementation of BaseRecord."""

    test_field: str
    test_value: int

    def get_primary_key_fields(self) -> list[str]:
        return ["city", "timestamp", "test_field"]


def test_city_coordinates_valid():
    """Test creating valid CityCoordinates."""
    coords = CityCoordinates(city="Helsinki", latitude=60.1699, longitude=24.9384)

    assert coords.city == "Helsinki"
    assert coords.latitude == 60.1699
    assert coords.longitude == 24.9384


def test_city_coordinates_required_fields():
    """Test that all CityCoordinates fields are required."""
    # Missing city
    with pytest.raises(ValidationError):
        CityCoordinates(latitude=60.1699, longitude=24.9384)

    # Missing latitude
    with pytest.raises(ValidationError):
        CityCoordinates(city="Helsinki", longitude=24.9384)

    # Missing longitude
    with pytest.raises(ValidationError):
        CityCoordinates(city="Helsinki", latitude=60.1699)


def test_city_coordinates_type_validation():
    """Test CityCoordinates type validation."""
    # Invalid latitude type
    with pytest.raises(ValidationError):
        CityCoordinates(city="Helsinki", latitude="invalid", longitude=24.9384)

    # Invalid longitude type
    with pytest.raises(ValidationError):
        CityCoordinates(city="Helsinki", latitude=60.1699, longitude="invalid")


def test_base_raw_response_abstract():
    """Test that BaseRawResponse get_data_field is abstract."""
    # This should work - concrete implementation
    response = SampleRawResponse(data={"key": "value"}, metadata={"source": "test"})
    assert response.get_data_field() == "data"

    # Test that BaseRawResponse itself raises NotImplementedError
    class IncompleteResponse(BaseRawResponse):
        data: dict

    incomplete = IncompleteResponse(data={})
    with pytest.raises(NotImplementedError):
        incomplete.get_data_field()


def test_test_raw_response_implementation():
    """Test our SampleRawResponse implementation."""
    response = SampleRawResponse(
        data={"temperature": 15.5, "humidity": 80},
        metadata={"timestamp": "2024-01-01T12:00:00Z", "source": "api"},
    )

    assert response.data == {"temperature": 15.5, "humidity": 80}
    assert response.metadata == {"timestamp": "2024-01-01T12:00:00Z", "source": "api"}
    assert response.get_data_field() == "data"


def test_base_record_with_explicit_datetime():
    """Test BaseRecord with explicitly provided datetime."""
    dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    ingested_dt = datetime(2024, 1, 1, 12, 30, 0, tzinfo=UTC)

    record = SampleRecord(
        city="Helsinki",
        timestamp=dt,
        date=date(2024, 1, 1),
        test_field="explicit_test",
        test_value=100,
        ingested_at=ingested_dt,
    )

    assert record.city == "Helsinki"
    assert record.timestamp == dt
    assert record.date == date(2024, 1, 1)
    assert record.test_field == "explicit_test"
    assert record.test_value == 100
    assert record.ingested_at == ingested_dt


def test_base_record_auto_ingested_at():
    """Test that BaseRecord auto-generates ingested_at when not provided."""
    dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)

    record = SampleRecord(
        city="Helsinki",
        timestamp=dt,
        date=date(2024, 1, 1),
        test_field="auto_test",
        test_value=200,
    )

    assert record.city == "Helsinki"
    assert record.timestamp == dt
    assert record.date == date(2024, 1, 1)
    assert record.test_field == "auto_test"
    assert record.test_value == 200

    # ingested_at should be auto-generated and recent
    assert record.ingested_at is not None
    assert isinstance(record.ingested_at, datetime)
    assert record.ingested_at.tzinfo == UTC

    # Should be very recent (within last minute)
    now = datetime.now(UTC)
    time_diff = (now - record.ingested_at).total_seconds()
    assert time_diff < 60


def test_base_record_required_fields():
    """Test that BaseRecord required fields are enforced."""
    dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)

    # Missing city
    with pytest.raises(ValidationError):
        SampleRecord(
            timestamp=dt,
            date=date(2024, 1, 1),
            test_field="missing_city",
            test_value=300,
        )

    # Missing timestamp
    with pytest.raises(ValidationError):
        SampleRecord(
            city="Helsinki",
            date=date(2024, 1, 1),
            test_field="missing_timestamp",
            test_value=400,
        )

    # Missing date
    with pytest.raises(ValidationError):
        SampleRecord(
            city="Helsinki",
            timestamp=dt,
            test_field="missing_date",
            test_value=500,
        )


def test_base_record_get_primary_key_fields():
    """Test get_primary_key_fields method."""
    dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)

    record = SampleRecord(
        city="Helsinki",
        timestamp=dt,
        date=date(2024, 1, 1),
        test_field="primary_key_test",
        test_value=600,
    )

    primary_keys = record.get_primary_key_fields()
    assert primary_keys == ["city", "timestamp", "test_field"]


def test_base_record_default_get_primary_key_fields():
    """Test default get_primary_key_fields implementation."""

    class DefaultRecord(BaseRecord):
        test_field: str

    dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)

    record = DefaultRecord(
        city="Helsinki",
        timestamp=dt,
        date=date(2024, 1, 1),
        test_field="default_test",
    )

    # Should return the default primary key fields
    primary_keys = record.get_primary_key_fields()
    assert primary_keys == ["city", "timestamp"]


def test_models_inheritance():
    """Test that our test models properly inherit from base classes."""
    assert issubclass(SampleRawResponse, BaseRawResponse)
    assert issubclass(SampleRecord, BaseRecord)

    # Test instance checks
    response = SampleRawResponse(data={}, metadata={})
    record = SampleRecord(
        city="Test",
        timestamp=datetime.now(UTC),
        date=date.today(),
        test_field="inheritance",
        test_value=700,
    )

    assert isinstance(response, BaseRawResponse)
    assert isinstance(record, BaseRecord)


def test_datetime_timezone_handling():
    """Test proper timezone handling in BaseRecord."""
    # Test with UTC timezone
    dt_utc = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    record_utc = SampleRecord(
        city="Helsinki",
        timestamp=dt_utc,
        date=date(2024, 1, 1),
        test_field="utc_test",
        test_value=800,
    )

    assert record_utc.timestamp.tzinfo == UTC

    # Test with naive datetime (should work but not recommended)
    dt_naive = datetime(2024, 1, 1, 12, 0, 0)
    record_naive = SampleRecord(
        city="Helsinki",
        timestamp=dt_naive,
        date=date(2024, 1, 1),
        test_field="naive_test",
        test_value=900,
    )

    assert record_naive.timestamp == dt_naive


def test_complex_data_in_raw_response():
    """Test BaseRawResponse with complex nested data."""
    complex_data = {
        "measurements": [
            {"time": "2024-01-01T00:00:00Z", "value": 15.5},
            {"time": "2024-01-01T01:00:00Z", "value": 16.2},
        ],
        "location": {
            "city": "Helsinki",
            "coordinates": {"lat": 60.1699, "lon": 24.9384},
        },
    }

    metadata = {"api_version": "v2", "source": "test_api", "request_id": "12345"}

    response = SampleRawResponse(data=complex_data, metadata=metadata)

    assert response.data["measurements"][0]["value"] == 15.5
    assert response.data["location"]["city"] == "Helsinki"
    assert response.metadata["api_version"] == "v2"
    assert response.get_data_field() == "data"
