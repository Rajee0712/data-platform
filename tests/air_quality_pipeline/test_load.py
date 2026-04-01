"""Tests for air_quality_pipeline.load module."""

from datetime import UTC, date, datetime

import pytest

from air_quality_pipeline.load import create_table, get_connection, load, upsert_records
from air_quality_pipeline.models import AirQualityRecord


@pytest.fixture
def conn():
    with get_connection(":memory:") as c:
        create_table(c)
        yield c


@pytest.fixture
def sample_records():
    return [
        AirQualityRecord(
            city="Helsinki",
            timestamp=datetime(2024, 1, 1, 0, 0, tzinfo=UTC),
            date=date(2024, 1, 1),
            pm2_5=6.3,
            pm10=9.5,
            carbon_monoxide=217.0,
            nitrogen_dioxide=10.7,
            ozone=42.0,
        ),
        AirQualityRecord(
            city="Helsinki",
            timestamp=datetime(2024, 1, 1, 1, 0, tzinfo=UTC),
            date=date(2024, 1, 1),
            pm2_5=6.5,
            pm10=9.2,
            carbon_monoxide=215.0,
            nitrogen_dioxide=10.4,
            ozone=38.0,
        ),
    ]


def test_create_table(conn):
    result = conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_name='air_quality_records'"
    ).fetchone()
    assert result is not None


def test_upsert_records(conn, sample_records):
    count = upsert_records(conn, sample_records)
    assert count == 2
    rows = conn.execute("SELECT * FROM air_quality.air_quality_records").fetchall()
    assert len(rows) == 2


def test_upsert_empty(conn):
    count = upsert_records(conn, [])
    assert count == 0


def test_upsert_deduplicates(conn, sample_records):
    upsert_records(conn, sample_records)
    upsert_records(conn, sample_records)
    rows = conn.execute("SELECT * FROM air_quality.air_quality_records").fetchall()
    assert len(rows) == 2


def test_load_creates_file(tmp_path, sample_records):
    db_path = str(tmp_path / "test.duckdb")
    count = load(sample_records, db_path=db_path)
    assert count == 2
    assert (tmp_path / "test.duckdb").exists()
