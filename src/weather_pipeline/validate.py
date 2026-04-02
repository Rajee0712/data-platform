"""Great Expectations validation for weather pipeline data."""

import great_expectations as gx
from loguru import logger

from shared.expectations.context import get_ephemeral_context, save_validation_results
from weather_pipeline.config import settings


def get_weather_dataframe(conn):
    """Fetch weather records from DuckDB as a pandas DataFrame."""
    return conn.execute("SELECT * FROM weather.weather_records").df()


def validate_weather_data(conn) -> bool:
    """Run Great Expectations suite against weather data in DuckDB."""
    logger.info("Running Great Expectations validation on weather data")

    df = get_weather_dataframe(conn)
    context = get_ephemeral_context()

    data_source = context.data_sources.add_pandas("weather_pandas")
    data_asset = data_source.add_dataframe_asset("weather_records")
    batch_definition = data_asset.add_batch_definition_whole_dataframe("batch")

    suite = context.suites.add(gx.ExpectationSuite(name="weather_suite"))
    suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="city"))
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToNotBeNull(column="timestamp")
    )
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToNotBeNull(column="temperature_c")
    )
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="temperature_c", min_value=-60.0, max_value=60.0
        )
    )
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="humidity_pct", min_value=0.0, max_value=100.0
        )
    )
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="windspeed_kmh", min_value=0.0, max_value=500.0
        )
    )
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="precipitation_mm", min_value=0.0, max_value=500.0
        )
    )
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeInSet(
            column="city", value_set=settings.cities_list
        )
    )
    suite.add_expectation(
        gx.expectations.ExpectCompoundColumnsToBeUnique(
            column_list=["city", "timestamp"]
        )
    )

    validation_definition = context.validation_definitions.add(
        gx.ValidationDefinition(
            name="weather_validation",
            data=batch_definition,
            suite=suite,
        )
    )

    results = validation_definition.run(batch_parameters={"dataframe": df})
    save_validation_results(results, "weather_validation")

    success = results.success

    if success:
        logger.info("Weather data validation passed ✅")
    else:
        logger.error("Weather data validation failed ❌")
        for result in results.results:
            if not result.success:
                logger.error(
                    f"Failed: {result.expectation_config.type} — {result.result}"
                )

    return success
