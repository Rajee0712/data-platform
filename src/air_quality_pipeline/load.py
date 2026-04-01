"""Load layer: write AirQualityRecords into DuckDB."""

from pathlib import Path

import duckdb
from loguru import logger

from air_quality_pipeline.config import settings
from air_quality_pipeline.models import AirQualityRecord

SCHEMA = "air_quality"


def get_connection(db_path: str | None = None) -> duckdb.DuckDBPyConnection:
    """Create a DuckDB connection, ensuring the parent directory exists."""
    path = db_path or settings.db_path
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(path)


def create_table(conn: duckdb.DuckDBPyConnection) -> None:
    """Create schema and air_quality_records table if they don't exist."""
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA}.air_quality_records (
            city                    VARCHAR,
            timestamp               TIMESTAMP,
            date                    DATE,
            parameter               VARCHAR,
            value                   DOUBLE,
            unit                    VARCHAR,
            coordinates_latitude    DOUBLE,
            coordinates_longitude   DOUBLE,
            ingested_at             TIMESTAMP,
            PRIMARY KEY (city, timestamp, parameter)
        )
    """)
    logger.debug("Schema and table air_quality.air_quality_records ready")


def upsert_records(
    conn: duckdb.DuckDBPyConnection,
    records: list[AirQualityRecord],
) -> int:
    """Insert records, replacing existing ones with same city+timestamp+parameter."""
    if not records:
        logger.warning("No records to load")
        return 0

    rows = [
        (
            r.city,
            r.timestamp,
            r.date,
            r.parameter,
            r.value,
            r.unit,
            r.coordinates_latitude,
            r.coordinates_longitude,
            r.ingested_at,
        )
        for r in records
    ]

    conn.executemany(
        f"""
        INSERT OR REPLACE INTO {SCHEMA}.air_quality_records
            (city, timestamp, date, parameter, value, unit,
             coordinates_latitude, coordinates_longitude, ingested_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        rows,
    )

    logger.info(f"Loaded {len(rows)} records into {SCHEMA}.air_quality_records")
    return len(rows)


def load(records: list[AirQualityRecord], db_path: str | None = None) -> int:
    """Main load entry point — create schema/table and upsert records."""
    with get_connection(db_path) as conn:
        create_table(conn)
        return upsert_records(conn, records)
