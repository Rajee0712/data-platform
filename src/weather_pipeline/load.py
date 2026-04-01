"""Load layer: write WeatherRecords into DuckDB."""

from pathlib import Path

import duckdb
from loguru import logger

from weather_pipeline.config import settings
from weather_pipeline.models import WeatherRecord

SCHEMA = "weather"


def get_connection(db_path: str | None = None) -> duckdb.DuckDBPyConnection:
    """Create a DuckDB connection, ensuring the parent directory exists."""
    path = db_path or settings.db_path
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(path)


def create_table(conn: duckdb.DuckDBPyConnection) -> None:
    """Create schema and weather_records table if they don't exist."""
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA}.weather_records (
            city                VARCHAR,
            timestamp           TIMESTAMP,
            date                DATE,
            temperature_c       DOUBLE,
            humidity_pct        DOUBLE,
            windspeed_kmh       DOUBLE,
            precipitation_mm    DOUBLE,
            ingested_at         TIMESTAMP,
            PRIMARY KEY (city, timestamp)
        )
    """)
    logger.debug("Schema and table weather.weather_records ready")


def upsert_records(
    conn: duckdb.DuckDBPyConnection,
    records: list[WeatherRecord],
) -> int:
    """Insert records, replacing existing ones with same city+timestamp."""
    if not records:
        logger.warning("No records to load")
        return 0

    rows = [
        (
            r.city,
            r.timestamp,
            r.date,
            r.temperature_c,
            r.humidity_pct,
            r.windspeed_kmh,
            r.precipitation_mm,
            r.ingested_at,
        )
        for r in records
    ]

    conn.executemany(
        f"""
        INSERT OR REPLACE INTO {SCHEMA}.weather_records
            (city, timestamp, date, temperature_c, humidity_pct,
             windspeed_kmh, precipitation_mm, ingested_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        rows,
    )

    logger.info(f"Loaded {len(rows)} records into {SCHEMA}.weather_records")
    return len(rows)


def load(records: list[WeatherRecord], db_path: str | None = None) -> int:
    """Main load entry point — create schema/table and upsert records."""
    with get_connection(db_path) as conn:
        create_table(conn)
        return upsert_records(conn, records)
