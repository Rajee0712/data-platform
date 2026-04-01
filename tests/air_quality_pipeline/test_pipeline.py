"""Tests for air_quality_pipeline.pipeline module."""

from unittest.mock import patch

from air_quality_pipeline.models import (
    AirQualityRecord,
    CityCoordinates,
    RawAirQualityResponse,
)
from air_quality_pipeline.pipeline import main


def test_main():
    """Test the main pipeline orchestration."""
    # Mock data
    mock_coords = CityCoordinates(city="Helsinki", latitude=60.1699, longitude=24.9384)
    mock_raw = RawAirQualityResponse(results=[])
    mock_extracted = [(mock_coords, mock_raw)]
    mock_records = []

    with (
        patch("air_quality_pipeline.pipeline.extract_all") as mock_extract,
        patch("air_quality_pipeline.pipeline.transform_all") as mock_transform,
        patch("air_quality_pipeline.pipeline.load") as mock_load,
        patch("air_quality_pipeline.pipeline.settings") as mock_settings,
    ):
        mock_settings.cities_list = ["Helsinki"]
        mock_extract.return_value = mock_extracted
        mock_transform.return_value = mock_records
        mock_load.return_value = 0

        # Run the pipeline
        main()

        # Verify all functions were called
        mock_extract.assert_called_once_with(["Helsinki"])
        mock_transform.assert_called_once_with(mock_extracted)
        mock_load.assert_called_once_with(mock_records)


def test_main_with_data():
    """Test main with actual data flow."""
    from datetime import UTC, date, datetime

    # Create more realistic mock data
    mock_coords = CityCoordinates(city="Helsinki", latitude=60.1699, longitude=24.9384)
    mock_raw = RawAirQualityResponse(
        results=[
            {
                "parameter": "pm25",
                "value": 10.5,
                "unit": "µg/m³",
                "date": {"utc": "2024-01-01T12:00:00Z"},
                "coordinates": {"latitude": 60.1699, "longitude": 24.9384},
            }
        ]
    )
    mock_extracted = [(mock_coords, mock_raw)]

    mock_record = AirQualityRecord(
        city="Helsinki",
        timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
        date=date(2024, 1, 1),
        parameter="pm25",
        value=10.5,
        unit="µg/m³",
        coordinates_latitude=60.1699,
        coordinates_longitude=24.9384,
    )
    mock_records = [mock_record]

    with (
        patch("air_quality_pipeline.pipeline.extract_all") as mock_extract,
        patch("air_quality_pipeline.pipeline.transform_all") as mock_transform,
        patch("air_quality_pipeline.pipeline.load") as mock_load,
        patch("air_quality_pipeline.pipeline.settings") as mock_settings,
    ):
        mock_settings.cities_list = ["Helsinki"]
        mock_extract.return_value = mock_extracted
        mock_transform.return_value = mock_records
        mock_load.return_value = 1

        # Run the pipeline
        main()

        # Verify correct data flow
        mock_extract.assert_called_once_with(["Helsinki"])
        mock_transform.assert_called_once_with(mock_extracted)
        mock_load.assert_called_once_with(mock_records)


def test_main_module_entrypoint():
    """Test __main__.py calls main()."""
    with (
        patch("air_quality_pipeline.pipeline.extract_all") as mock_extract,
        patch("air_quality_pipeline.pipeline.transform_all") as mock_transform,
        patch("air_quality_pipeline.pipeline.load") as mock_load,
    ):
        mock_extract.return_value = []
        mock_transform.return_value = []
        mock_load.return_value = 0
        import runpy
        import sys

        sys.modules.pop("air_quality_pipeline.__main__", None)
        runpy.run_module("air_quality_pipeline", run_name="__main__")
        mock_extract.assert_called_once()
