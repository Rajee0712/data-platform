"""Tests for air_quality_pipeline.load module."""

from datetime import UTC, date, datetime

import duckdb

from air_quality_pipeline.load import create_table, get_connection, load, upsert_records
from air_quality_pipeline.models import AirQualityRecord


def test_get_connection():
    """Test creating a DuckDB connection."""
    conn = get_connection(":memory:")
    assert isinstance(conn, duckdb.DuckDBPyConnection)
    conn.close()


def test_create_table():
    """Test creating the air_quality_records table."""
    conn = get_connection(":memory:")
    create_table(conn)

    # Check that table exists by querying schema
    result = conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_name = 'air_quality_records'"
    ).fetchone()
    assert result is not None
    assert result[0] == "air_quality_records"
    conn.close()


def test_upsert_records():
    """Test inserting air quality records."""
    conn = get_connection(":memory:")
    create_table(conn)

    records = [
        AirQualityRecord(
            city="Helsinki",
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            date=date(2024, 1, 1),
            parameter="pm25",
            value=10.5,
            unit="µg/m³",
            coordinates_latitude=60.1699,
            coordinates_longitude=24.9384,
        ),
        AirQualityRecord(
            city="Helsinki",
            timestamp=datetime(2024, 1, 1, 13, 0, 0, tzinfo=UTC),
            date=date(2024, 1, 1),
            parameter="pm10",
            value=20.0,
            unit="µg/m³",
            coordinates_latitude=60.1699,
            coordinates_longitude=24.9384,
        ),
    ]

    count = upsert_records(conn, records)
    assert count == 2

    # Verify records were inserted
    result = conn.execute(
        "SELECT COUNT(*) FROM air_quality.air_quality_records"
    ).fetchone()
    assert result[0] == 2

    # Verify data integrity
    result = conn.execute(
        "SELECT city, parameter, value FROM air_quality.air_quality_records ORDER BY timestamp"
    ).fetchall()
    assert result[0] == ("Helsinki", "pm25", 10.5)
    assert result[1] == ("Helsinki", "pm10", 20.0)

    conn.close()


def test_upsert_records_empty():
    """Test upserting with empty record list."""
    conn = get_connection(":memory:")
    create_table(conn)

    count = upsert_records(conn, [])
    assert count == 0

    result = conn.execute(
        "SELECT COUNT(*) FROM air_quality.air_quality_records"
    ).fetchone()
    assert result[0] == 0
    conn.close()


def test_upsert_records_duplicate():
    """Test that duplicate records are replaced (INSERT OR REPLACE behavior)."""
    conn = get_connection(":memory:")
    create_table(conn)

    # Insert initial record
    record1 = AirQualityRecord(
        city="Helsinki",
        timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
        date=date(2024, 1, 1),
        parameter="pm25",
        value=10.5,
        unit="µg/m³",
        coordinates_latitude=60.1699,
        coordinates_longitude=24.9384,
    )
    upsert_records(conn, [record1])

    # Insert duplicate with different value
    record2 = AirQualityRecord(
        city="Helsinki",
        timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
        date=date(2024, 1, 1),
        parameter="pm25",
        value=12.0,  # Different value
        unit="µg/m³",
        coordinates_latitude=60.1699,
        coordinates_longitude=24.9384,
    )
    upsert_records(conn, [record2])

    # Should still have only 1 record, but with updated value
    result = conn.execute(
        "SELECT COUNT(*) FROM air_quality.air_quality_records"
    ).fetchone()
    assert result[0] == 1

    result = conn.execute(
        "SELECT value FROM air_quality.air_quality_records"
    ).fetchone()
    assert result[0] == 12.0  # Updated value

    conn.close()


def test_load():
    """Test the main load function."""
    records = [
        AirQualityRecord(
            city="Helsinki",
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            date=date(2024, 1, 1),
            parameter="pm25",
            value=10.5,
            unit="µg/m³",
            coordinates_latitude=60.1699,
            coordinates_longitude=24.9384,
        )
    ]

    count = load(records, ":memory:")
    assert count == 1


def test_load_empty():
    """Test load with empty records."""
    count = load([], ":memory:")
    assert count == 0
