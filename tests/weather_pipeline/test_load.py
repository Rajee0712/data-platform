"""Unit tests for the load layer."""

from datetime import datetime

import pytest

from weather_pipeline.load import create_table, get_connection, load, upsert_records
from weather_pipeline.models import WeatherRecord


@pytest.fixture
def conn():
    """In-memory DuckDB connection for tests — no files created."""
    with get_connection(":memory:") as c:
        create_table(c)
        yield c


@pytest.fixture
def sample_records():
    return [
        WeatherRecord(
            city="Helsinki",
            timestamp=datetime(2024, 1, 15, 0, 0),
            date=datetime(2024, 1, 15).date(),
            temperature_c=-3.2,
            humidity_pct=85.0,
            windspeed_kmh=12.0,
            precipitation_mm=0.0,
        ),
        WeatherRecord(
            city="Helsinki",
            timestamp=datetime(2024, 1, 15, 1, 0),
            date=datetime(2024, 1, 15).date(),
            temperature_c=-3.5,
            humidity_pct=86.0,
            windspeed_kmh=11.5,
            precipitation_mm=0.1,
        ),
    ]


def test_create_table(conn):
    result = conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_name='weather_records'"
    ).fetchone()
    assert result is not None


def test_upsert_records(conn, sample_records):
    count = upsert_records(conn, sample_records)
    assert count == 2
    rows = conn.execute("SELECT * FROM weather.weather_records").fetchall()
    assert len(rows) == 2


def test_upsert_empty(conn):
    count = upsert_records(conn, [])
    assert count == 0


def test_upsert_deduplicates(conn, sample_records):
    """Inserting same records twice should not duplicate rows."""
    upsert_records(conn, sample_records)
    upsert_records(conn, sample_records)
    rows = conn.execute("SELECT * FROM weather.weather_records").fetchall()
    assert len(rows) == 2  # still 2, not 4


def test_load_creates_file(tmp_path, sample_records):
    """load() should create the DuckDB file on disk."""
    db_path = str(tmp_path / "test.duckdb")
    count = load(sample_records, db_path=db_path)
    assert count == 2
    assert (tmp_path / "test.duckdb").exists()
