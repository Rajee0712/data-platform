"""Shared loading utilities for all pipelines."""

from pathlib import Path

import duckdb
from loguru import logger

from shared.models import BaseRecord


def get_connection(db_path: str) -> duckdb.DuckDBPyConnection:
    """Create a DuckDB connection, ensuring the parent directory exists."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(db_path)


def create_table_generic(
    conn: duckdb.DuckDBPyConnection, table_name: str, schema_sql: str
) -> None:
    """Create a table with the given schema if it doesn't exist."""
    conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({schema_sql})")
    logger.debug(f"Table {table_name} ready")


def upsert_records_generic[T: BaseRecord](
    conn: duckdb.DuckDBPyConnection,
    table_name: str,
    records: list[T],
    field_mapping: dict[str, str],
) -> int:
    """Insert records, replacing existing ones with same primary key."""
    if not records:
        logger.warning("No records to load")
        return 0

    # Convert pydantic models to tuples based on field mapping
    rows = []
    for record in records:
        row = tuple(getattr(record, field) for field in field_mapping)
        rows.append(row)

    # Build SQL placeholders
    placeholders = ", ".join(["?" for _ in field_mapping])
    fields = ", ".join(field_mapping.values())

    conn.executemany(
        f"INSERT OR REPLACE INTO {table_name} ({fields}) VALUES ({placeholders})",
        rows,
    )

    logger.info(f"Loaded {len(rows)} records into {table_name}")
    return len(rows)


def load_generic[T: BaseRecord](
    records: list[T],
    db_path: str,
    table_name: str,
    schema_sql: str,
    field_mapping: dict[str, str],
) -> int:
    """Generic load entry point — create table and upsert records."""
    with get_connection(db_path) as conn:
        create_table_generic(conn, table_name, schema_sql)
        return upsert_records_generic(conn, table_name, records, field_mapping)
