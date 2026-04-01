"""Load layer: write WeatherRecords into DuckDB."""

import duckdb
from loguru import logger

from shared.load_utils import get_connection
from weather_pipeline.config import settings
from weather_pipeline.models import WeatherRecord

# Field mapping from model attributes to database columns
WEATHER_FIELD_MAPPING = {
    "city": "city",
    "timestamp": "timestamp",
    "date": "date",
    "temperature_c": "temperature_c",
    "humidity_pct": "humidity_pct",
    "windspeed_kmh": "windspeed_kmh",
    "precipitation_mm": "precipitation_mm",
    "ingested_at": "ingested_at",
}


def create_schema_and_table(conn: duckdb.DuckDBPyConnection) -> None:
    """Create schema and weather_records table if they don't exist."""
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {settings.db_schema}")
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {settings.db_schema}.weather_records (
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
    logger.debug(f"Schema and table {settings.db_schema}.weather_records ready")


def upsert_records(
    conn: duckdb.DuckDBPyConnection,
    records: list[WeatherRecord],
) -> int:
    """Insert records, replacing existing ones with same city+timestamp."""
    if not records:
        logger.warning("No records to load")
        return 0

    rows = [
        tuple(getattr(record, field) for field in WEATHER_FIELD_MAPPING)
        for record in records
    ]

    placeholders = ", ".join(["?" for _ in WEATHER_FIELD_MAPPING])
    fields = ", ".join(WEATHER_FIELD_MAPPING.values())
    table_name = f"{settings.db_schema}.weather_records"

    conn.executemany(
        f"INSERT OR REPLACE INTO {table_name} ({fields}) VALUES ({placeholders})",
        rows,
    )

    logger.info(f"Loaded {len(rows)} records into {table_name}")
    return len(rows)


def load(records: list[WeatherRecord], db_path: str | None = None) -> int:
    """Main load entry point — create schema/table and upsert records."""
    db_path = db_path or settings.db_path
    with get_connection(db_path) as conn:
        create_schema_and_table(conn)
        return upsert_records(conn, records)
