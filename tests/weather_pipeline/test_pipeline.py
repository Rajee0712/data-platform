"""Unit tests for the pipeline orchestrator."""

from unittest.mock import MagicMock, patch

from weather_pipeline.pipeline import main


@patch("weather_pipeline.pipeline.validate_weather_data")
@patch("weather_pipeline.pipeline.extract_all")
@patch("weather_pipeline.pipeline.transform_all")
@patch("weather_pipeline.pipeline.load")
def test_main_calls_etl_in_order(
    mock_load, mock_transform, mock_extract, mock_validate
):
    """Pipeline should call extract → transform → load in order."""
    mock_extract.return_value = [MagicMock()]
    mock_transform.return_value = [MagicMock()]
    mock_load.return_value = 24
    mock_validate.return_value = True
    main()
    mock_extract.assert_called_once()
    mock_transform.assert_called_once_with(mock_extract.return_value)
    mock_load.assert_called_once_with(mock_transform.return_value)


@patch("weather_pipeline.pipeline.validate_weather_data")
@patch("weather_pipeline.pipeline.extract_all")
@patch("weather_pipeline.pipeline.transform_all")
@patch("weather_pipeline.pipeline.load")
def test_main_passes_cities_from_settings(
    mock_load, mock_transform, mock_extract, mock_validate
):
    """Pipeline should pass cities from settings to extract_all."""
    mock_extract.return_value = []
    mock_transform.return_value = []
    mock_load.return_value = 0
    mock_validate.return_value = True
    main()
    called_cities = mock_extract.call_args[0][0]
    assert isinstance(called_cities, list)
    assert len(called_cities) > 0


@patch("weather_pipeline.pipeline.validate_weather_data")
@patch("weather_pipeline.pipeline.extract_all")
@patch("weather_pipeline.pipeline.transform_all")
@patch("weather_pipeline.pipeline.load")
def test_main_empty_results(mock_load, mock_transform, mock_extract, mock_validate):
    """Pipeline should handle no data gracefully."""
    mock_extract.return_value = []
    mock_transform.return_value = []
    mock_load.return_value = 0
    mock_validate.return_value = True
    main()
    mock_load.assert_called_once_with([])


def test_main_module_entrypoint():
    """Test __main__.py is importable and calls main."""
    with (
        patch("weather_pipeline.pipeline.extract_all") as mock_extract,
        patch("weather_pipeline.pipeline.transform_all") as mock_transform,
        patch("weather_pipeline.pipeline.load") as mock_load,
        patch("weather_pipeline.pipeline.validate_weather_data") as mock_validate,
    ):
        mock_extract.return_value = []
        mock_transform.return_value = []
        mock_load.return_value = 0
        mock_validate.return_value = True
        import runpy
        import sys

        sys.modules.pop("weather_pipeline.__main__", None)
        runpy.run_module("weather_pipeline", run_name="__main__")
        mock_extract.assert_called_once()
