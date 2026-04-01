"""Load layer: write AirQualityRecords into DuckDB."""

import duckdb
from loguru import logger

from air_quality_pipeline.config import settings
from air_quality_pipeline.models import AirQualityRecord
from shared.load_utils import get_connection

# Field mapping from model attributes to database columns
AIR_QUALITY_FIELD_MAPPING = {
    "city": "city",
    "timestamp": "timestamp",
    "date": "date",
    "pm2_5": "pm2_5",
    "pm10": "pm10",
    "carbon_monoxide": "carbon_monoxide",
    "nitrogen_dioxide": "nitrogen_dioxide",
    "ozone": "ozone",
    "ingested_at": "ingested_at",
}


def create_schema_and_table(conn: duckdb.DuckDBPyConnection) -> None:
    """Create schema and air_quality_records table if they don't exist."""
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {settings.db_schema}")
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {settings.db_schema}.air_quality_records (
            city                VARCHAR,
            timestamp           TIMESTAMP,
            date                DATE,
            pm2_5               DOUBLE,
            pm10                DOUBLE,
            carbon_monoxide     DOUBLE,
            nitrogen_dioxide    DOUBLE,
            ozone               DOUBLE,
            ingested_at         TIMESTAMP,
            PRIMARY KEY (city, timestamp)
        )
    """)
    logger.debug(f"Schema and table {settings.db_schema}.air_quality_records ready")


def upsert_records(
    conn: duckdb.DuckDBPyConnection,
    records: list[AirQualityRecord],
) -> int:
    """Insert records, replacing existing ones with same city+timestamp."""
    if not records:
        logger.warning("No records to load")
        return 0

    rows = [
        tuple(getattr(record, field) for field in AIR_QUALITY_FIELD_MAPPING)
        for record in records
    ]

    placeholders = ", ".join(["?" for _ in AIR_QUALITY_FIELD_MAPPING])
    fields = ", ".join(AIR_QUALITY_FIELD_MAPPING.values())
    table_name = f"{settings.db_schema}.air_quality_records"

    conn.executemany(
        f"INSERT OR REPLACE INTO {table_name} ({fields}) VALUES ({placeholders})",
        rows,
    )

    logger.info(f"Loaded {len(rows)} records into {table_name}")
    return len(rows)


def load(records: list[AirQualityRecord], db_path: str | None = None) -> int:
    """Main load entry point — create schema/table and upsert records."""
    db_path = db_path or settings.db_path
    with get_connection(db_path) as conn:
        create_schema_and_table(conn)
        return upsert_records(conn, records)
