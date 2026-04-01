"""Tests for air_quality_pipeline.pipeline module."""

from unittest.mock import MagicMock, patch

from air_quality_pipeline.pipeline import main


@patch("air_quality_pipeline.pipeline.extract_all")
@patch("air_quality_pipeline.pipeline.transform_all")
@patch("air_quality_pipeline.pipeline.load")
def test_main_calls_etl_in_order(mock_load, mock_transform, mock_extract):
    mock_extract.return_value = [MagicMock()]
    mock_transform.return_value = [MagicMock()]
    mock_load.return_value = 24
    main()
    mock_extract.assert_called_once()
    mock_transform.assert_called_once_with(mock_extract.return_value)
    mock_load.assert_called_once_with(mock_transform.return_value)


@patch("air_quality_pipeline.pipeline.extract_all")
@patch("air_quality_pipeline.pipeline.transform_all")
@patch("air_quality_pipeline.pipeline.load")
def test_main_passes_cities_from_settings(mock_load, mock_transform, mock_extract):
    mock_extract.return_value = []
    mock_transform.return_value = []
    mock_load.return_value = 0
    main()
    called_cities = mock_extract.call_args[0][0]
    assert isinstance(called_cities, list)
    assert len(called_cities) > 0


@patch("air_quality_pipeline.pipeline.extract_all")
@patch("air_quality_pipeline.pipeline.transform_all")
@patch("air_quality_pipeline.pipeline.load")
def test_main_empty_results(mock_load, mock_transform, mock_extract):
    mock_extract.return_value = []
    mock_transform.return_value = []
    mock_load.return_value = 0
    main()
    mock_load.assert_called_once_with([])


def test_main_module_entrypoint():
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
