"""Tests for shared.load_utils module."""

from datetime import UTC, date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import duckdb

from shared.load_utils import (
    create_table_generic,
    get_connection,
    load_generic,
    upsert_records_generic,
)
from shared.models import BaseRecord


class SampleRecord(BaseRecord):
    """Test record for testing load utilities."""

    test_field: str
    test_value: int

    def get_primary_key_fields(self) -> list[str]:
        return ["city", "timestamp"]


def test_get_connection_memory():
    """Test creating in-memory DuckDB connection."""
    conn = get_connection(":memory:")
    assert isinstance(conn, duckdb.DuckDBPyConnection)

    # Test that we can execute queries
    result = conn.execute("SELECT 1 as test").fetchone()
    assert result[0] == 1
    conn.close()


def test_get_connection_file_path():
    """Test creating file-based DuckDB connection with directory creation."""
    with TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "subdir" / "test.duckdb"

        # Directory shouldn't exist initially
        assert not db_path.parent.exists()

        conn = get_connection(str(db_path))
        assert isinstance(conn, duckdb.DuckDBPyConnection)

        # Directory should be created
        assert db_path.parent.exists()

        # Test that we can use the connection
        result = conn.execute("SELECT 1 as test").fetchone()
        assert result[0] == 1
        conn.close()


def test_create_table_generic():
    """Test creating a table with generic schema."""
    conn = get_connection(":memory:")

    schema_sql = """
        id INTEGER PRIMARY KEY,
        name VARCHAR,
        value DOUBLE
    """

    create_table_generic(conn, "test_table", schema_sql)

    # Verify table exists
    result = conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_name = 'test_table'"
    ).fetchone()
    assert result is not None
    assert result[0] == "test_table"

    conn.close()


def test_upsert_records_generic():
    """Test upserting records with generic function."""
    conn = get_connection(":memory:")

    # Create test table
    schema_sql = """
        city VARCHAR,
        timestamp TIMESTAMP,
        date DATE,
        test_field VARCHAR,
        test_value INTEGER,
        ingested_at TIMESTAMP,
        PRIMARY KEY (city, timestamp)
    """
    create_table_generic(conn, "test_records", schema_sql)

    # Create test records
    records = [
        SampleRecord(
            city="Helsinki",
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            date=date(2024, 1, 1),
            test_field="test1",
            test_value=10,
        ),
        SampleRecord(
            city="Tampere",
            timestamp=datetime(2024, 1, 1, 13, 0, 0, tzinfo=UTC),
            date=date(2024, 1, 1),
            test_field="test2",
            test_value=20,
        ),
    ]

    field_mapping = {
        "city": "city",
        "timestamp": "timestamp",
        "date": "date",
        "test_field": "test_field",
        "test_value": "test_value",
        "ingested_at": "ingested_at",
    }

    # Upsert records
    count = upsert_records_generic(conn, "test_records", records, field_mapping)
    assert count == 2

    # Verify records were inserted
    result = conn.execute("SELECT COUNT(*) FROM test_records").fetchone()
    assert result[0] == 2

    # Verify data integrity
    result = conn.execute(
        "SELECT city, test_field, test_value FROM test_records ORDER BY city"
    ).fetchall()
    assert result[0] == ("Helsinki", "test1", 10)
    assert result[1] == ("Tampere", "test2", 20)

    conn.close()


def test_upsert_records_generic_empty():
    """Test upserting with empty record list."""
    conn = get_connection(":memory:")

    schema_sql = "id INTEGER PRIMARY KEY"
    create_table_generic(conn, "empty_table", schema_sql)

    count = upsert_records_generic(conn, "empty_table", [], {"id": "id"})
    assert count == 0

    # Verify table is empty
    result = conn.execute("SELECT COUNT(*) FROM empty_table").fetchone()
    assert result[0] == 0

    conn.close()


def test_upsert_records_generic_replace():
    """Test that upsert replaces existing records with same primary key."""
    conn = get_connection(":memory:")

    # Create test table
    schema_sql = """
        city VARCHAR,
        timestamp TIMESTAMP,
        date DATE,
        test_field VARCHAR,
        test_value INTEGER,
        ingested_at TIMESTAMP,
        PRIMARY KEY (city, timestamp)
    """
    create_table_generic(conn, "test_records", schema_sql)

    field_mapping = {
        "city": "city",
        "timestamp": "timestamp",
        "date": "date",
        "test_field": "test_field",
        "test_value": "test_value",
        "ingested_at": "ingested_at",
    }

    # Insert initial record
    initial_record = SampleRecord(
        city="Helsinki",
        timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
        date=date(2024, 1, 1),
        test_field="original",
        test_value=100,
    )
    upsert_records_generic(conn, "test_records", [initial_record], field_mapping)

    # Insert duplicate with different values
    updated_record = SampleRecord(
        city="Helsinki",
        timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
        date=date(2024, 1, 1),
        test_field="updated",
        test_value=200,
    )
    upsert_records_generic(conn, "test_records", [updated_record], field_mapping)

    # Should still have only 1 record, but with updated values
    result = conn.execute("SELECT COUNT(*) FROM test_records").fetchone()
    assert result[0] == 1

    result = conn.execute("SELECT test_field, test_value FROM test_records").fetchone()
    assert result[0] == "updated"
    assert result[1] == 200

    conn.close()


def test_load_generic():
    """Test the complete load_generic workflow."""
    with TemporaryDirectory() as temp_dir:
        db_path = str(Path(temp_dir) / "test.duckdb")

        # Create test records
        records = [
            SampleRecord(
                city="Helsinki",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
                date=date(2024, 1, 1),
                test_field="load_test",
                test_value=42,
            ),
        ]

        schema_sql = """
            city VARCHAR,
            timestamp TIMESTAMP,
            date DATE,
            test_field VARCHAR,
            test_value INTEGER,
            ingested_at TIMESTAMP,
            PRIMARY KEY (city, timestamp)
        """

        field_mapping = {
            "city": "city",
            "timestamp": "timestamp",
            "date": "date",
            "test_field": "test_field",
            "test_value": "test_value",
            "ingested_at": "ingested_at",
        }

        # Load records
        count = load_generic(
            records=records,
            db_path=db_path,
            table_name="test_table",
            schema_sql=schema_sql,
            field_mapping=field_mapping,
        )

        assert count == 1

        # Verify by connecting to the database
        with get_connection(db_path) as conn:
            result = conn.execute("SELECT COUNT(*) FROM test_table").fetchone()
            assert result[0] == 1

            result = conn.execute(
                "SELECT city, test_field, test_value FROM test_table"
            ).fetchone()
            assert result[0] == "Helsinki"
            assert result[1] == "load_test"
            assert result[2] == 42


def test_load_generic_empty_records():
    """Test load_generic with empty records list."""
    with TemporaryDirectory() as temp_dir:
        db_path = str(Path(temp_dir) / "empty.duckdb")

        count = load_generic(
            records=[],
            db_path=db_path,
            table_name="empty_table",
            schema_sql="id INTEGER PRIMARY KEY",
            field_mapping={"id": "id"},
        )

        assert count == 0


def test_field_mapping_keys_iteration():
    """Test that field mapping keys are properly iterated."""
    conn = get_connection(":memory:")

    # Create test table with specific column order
    schema_sql = """
        first_col VARCHAR,
        second_col INTEGER,
        third_col VARCHAR,
        PRIMARY KEY (third_col, second_col)
    """
    create_table_generic(conn, "order_test", schema_sql)

    # Create record with specific field order
    record = SampleRecord(
        city="Test",
        timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
        date=date(2024, 1, 1),
        test_field="field_value",
        test_value=999,
    )

    # Field mapping with specific order
    field_mapping = {
        "test_field": "first_col",
        "test_value": "second_col",
        "city": "third_col",
    }

    count = upsert_records_generic(conn, "order_test", [record], field_mapping)
    assert count == 1

    # Verify values are in correct columns
    result = conn.execute(
        "SELECT first_col, second_col, third_col FROM order_test"
    ).fetchone()
    assert result[0] == "field_value"  # test_field -> first_col
    assert result[1] == 999  # test_value -> second_col
    assert result[2] == "Test"  # city -> third_col

    conn.close()
