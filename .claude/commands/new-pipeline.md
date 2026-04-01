Create a new pipeline called $ARGUMENTS following the same structure as weather_pipeline.

Steps:
1. Create src/$ARGUMENTS/ with __init__.py, config.py, models.py, extract.py, transform.py, load.py, pipeline.py, __main__.py
2. Create tests/$ARGUMENTS/ with test files for each module
3. Import cities from shared.cities
4. Follow the same ELT pattern as weather_pipeline
5. Add entry point to pyproject.toml
