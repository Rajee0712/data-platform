"""Unit tests for weather pipeline validation."""

from unittest.mock import MagicMock, patch

import pandas as pd

from weather_pipeline.validate import get_weather_dataframe, validate_weather_data


def make_mock_context(mock_result):
    """Helper to build a mock GE context."""
    mock_ctx = MagicMock()
    mock_ctx.suites.add.return_value = MagicMock()
    mock_ctx.data_sources.add_pandas.return_value.add_dataframe_asset.return_value.add_batch_definition_whole_dataframe.return_value = MagicMock()
    mock_ctx.validation_definitions.add.return_value.run.return_value = mock_result
    return mock_ctx


def test_validate_weather_data_success():
    """Test validate returns True on success."""
    conn = MagicMock()
    conn.execute.return_value.df.return_value = pd.DataFrame(
        {
            "city": ["Helsinki"],
            "timestamp": ["2024-01-01 00:00:00"],
            "temperature_c": [1.0],
        }
    )

    mock_result = MagicMock()
    mock_result.success = True
    mock_result.results = []

    with (
        patch("weather_pipeline.validate.get_ephemeral_context") as mock_context,
        patch("weather_pipeline.validate.save_validation_results") as mock_save,
        patch("weather_pipeline.validate.gx") as mock_gx,
    ):
        mock_context.return_value = make_mock_context(mock_result)
        mock_gx.ValidationDefinition.return_value = MagicMock()
        mock_gx.ExpectationSuite.return_value = MagicMock()
        mock_context.return_value.validation_definitions.add.return_value.run.return_value = mock_result

        result = validate_weather_data(conn)

    assert result is True
    mock_save.assert_called_once_with(mock_result, "weather_validation")


def test_validate_weather_data_failure():
    """Test validate returns False on failure."""
    conn = MagicMock()
    conn.execute.return_value.df.return_value = pd.DataFrame(
        {
            "city": ["Helsinki"],
            "timestamp": ["2024-01-01 00:00:00"],
            "temperature_c": [1.0],
        }
    )

    failed_exp = MagicMock()
    failed_exp.success = False
    failed_exp.expectation_config.type = "expect_column_values_to_not_be_null"
    failed_exp.result = {"unexpected_count": 1}

    mock_result = MagicMock()
    mock_result.success = False
    mock_result.results = [failed_exp]

    with (
        patch("weather_pipeline.validate.get_ephemeral_context") as mock_context,
        patch("weather_pipeline.validate.save_validation_results") as mock_save,
        patch("weather_pipeline.validate.gx") as mock_gx,
    ):
        mock_context.return_value = make_mock_context(mock_result)
        mock_gx.ValidationDefinition.return_value = MagicMock()
        mock_gx.ExpectationSuite.return_value = MagicMock()
        mock_context.return_value.validation_definitions.add.return_value.run.return_value = mock_result

        result = validate_weather_data(conn)

    assert result is False
    mock_save.assert_called_once_with(mock_result, "weather_validation")


def test_get_weather_dataframe():
    """Test that get_weather_dataframe calls correct SQL."""
    conn = MagicMock()
    conn.execute.return_value.df.return_value = pd.DataFrame()
    get_weather_dataframe(conn)
    conn.execute.assert_called_once_with("SELECT * FROM weather.weather_records")


def test_validate_adds_correct_number_of_expectations():
    """Test that 9 expectations are added for weather data."""
    conn = MagicMock()
    conn.execute.return_value.df.return_value = pd.DataFrame()

    mock_result = MagicMock()
    mock_result.success = True
    mock_result.results = []

    mock_suite = MagicMock()

    with (
        patch("weather_pipeline.validate.get_ephemeral_context") as mock_context,
        patch("weather_pipeline.validate.save_validation_results"),
        patch("weather_pipeline.validate.gx") as mock_gx,
    ):
        mock_ctx = make_mock_context(mock_result)
        mock_ctx.suites.add.return_value = mock_suite
        mock_context.return_value = mock_ctx
        mock_gx.ValidationDefinition.return_value = MagicMock()
        mock_gx.ExpectationSuite.return_value = MagicMock()
        mock_ctx.validation_definitions.add.return_value.run.return_value = mock_result

        validate_weather_data(conn)

    assert mock_suite.add_expectation.call_count == 9
