"""Load layer: write WeatherRecords into DuckDB."""

from pathlib import Path

import duckdb
from loguru import logger

from weather_pipeline.config import settings
from weather_pipeline.models import WeatherRecord


def get_connection(db_path: str | None = None) -> duckdb.DuckDBPyConnection:
    """Create a DuckDB connection, ensuring the parent directory exists."""
    path = db_path or settings.db_path
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(path)


def create_table(conn: duckdb.DuckDBPyConnection) -> None:
    """Create the weather_records table if it doesn't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS weather_records (
            city            VARCHAR,
            timestamp       TIMESTAMP,
            date            DATE,
            temperature_c   DOUBLE,
            humidity_pct    DOUBLE,
            windspeed_kmh   DOUBLE,
            precipitation_mm DOUBLE,
            ingested_at     TIMESTAMP,
            PRIMARY KEY (city, timestamp)
        )
    """)
    logger.debug("Table weather_records ready")


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
        """
        INSERT OR REPLACE INTO weather_records
            (city, timestamp, date, temperature_c, humidity_pct,
             windspeed_kmh, precipitation_mm, ingested_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        rows,
    )

    logger.info(f"Loaded {len(rows)} records into DuckDB")
    return len(rows)


def load(records: list[WeatherRecord], db_path: str | None = None) -> int:
    """Main load entry point — create table and upsert records."""
    with get_connection(db_path) as conn:
        create_table(conn)
        return upsert_records(conn, records)
