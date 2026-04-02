"""Great Expectations validation for air quality pipeline data."""

import great_expectations as gx
from loguru import logger

from air_quality_pipeline.config import settings
from shared.expectations.context import get_ephemeral_context, save_validation_results


def get_air_quality_dataframe(conn):
    """Fetch air quality records from DuckDB as a pandas DataFrame."""
    return conn.execute("SELECT * FROM air_quality.air_quality_records").df()


def validate_air_quality_data(conn) -> bool:
    """Run Great Expectations suite against air quality data in DuckDB."""
    logger.info("Running Great Expectations validation on air quality data")

    df = get_air_quality_dataframe(conn)
    context = get_ephemeral_context()

    data_source = context.data_sources.add_pandas("air_quality_pandas")
    data_asset = data_source.add_dataframe_asset("air_quality_records")
    batch_definition = data_asset.add_batch_definition_whole_dataframe("batch")

    suite = context.suites.add(gx.ExpectationSuite(name="air_quality_suite"))
    suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="city"))
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToNotBeNull(column="timestamp")
    )
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="pm2_5", min_value=0.0, max_value=1000.0, mostly=0.95
        )
    )
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="pm10", min_value=0.0, max_value=1000.0, mostly=0.95
        )
    )
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="ozone", min_value=0.0, max_value=500.0, mostly=0.95
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
            name="air_quality_validation",
            data=batch_definition,
            suite=suite,
        )
    )

    results = validation_definition.run(batch_parameters={"dataframe": df})
    save_validation_results(results, "air_quality_validation")
    success = results.success

    if success:
        logger.info("Air quality data validation passed ✅")
    else:
        logger.error("Air quality data validation failed ❌")
        for result in results.results:
            if not result.success:
                logger.error(
                    f"Failed: {result.expectation_config.type} — {result.result}"
                )

    return success
