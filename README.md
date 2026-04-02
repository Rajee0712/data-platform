# Data Platform

![CI](https://github.com/Rajee0712/data-platform/actions/workflows/ci.yml/badge.svg)
[![Coverage](https://codecov.io/gh/Rajee0712/data-platform/branch/main/graph/badge.svg)](https://codecov.io/gh/Rajee0712/data-platform)
![Python](https://img.shields.io/badge/dynamic/toml?url=https://raw.githubusercontent.com/Rajee0712/data-platform/main/pyproject.toml&query=project.requires-python&label=python)
![Version](https://img.shields.io/badge/dynamic/toml?url=https://raw.githubusercontent.com/Rajee0712/data-platform/main/pyproject.toml&query=project.version&label=version)
![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)
![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)
![License](https://img.shields.io/badge/license-MIT-green)


A production-grade data platform with multiple ELT pipelines that fetch data from
various APIs and load it into DuckDB for cross-source analysis.

## Validation Report

Data quality is validated using [Great Expectations](https://greatexpectations.io/) after every pipeline run.

[![Validation Report](https://img.shields.io/badge/Validation-Report-blue)](https://rajee0712.github.io/data-platform/validation/)

To generate the report locally run `make run_all && make report`

## Available Pipelines

### Weather Pipeline
Fetches hourly weather data from [Open-Meteo API](https://open-meteo.com/)
```bash
# Run weather pipeline
python -m weather_pipeline
# Or via entry point
weather-pipeline
```

### Air Quality Pipeline
Fetches air quality measurements from [Open-Meteo Air Quality API](https://open-meteo.com/en/docs/air-quality-api)
```bash
# Run air quality pipeline
python -m air_quality_pipeline
# Or via entry point
air-quality-pipeline
```

## Stack
- **Extract** — Multiple Open-Meteo APIs (Weather, Air Quality) via httpx + tenacity retries
- **Transform** — Pydantic models for typed, validated records
- **Load** — DuckDB with idempotent upserts
- **Shared** — Common utilities for extraction, loading, and configuration
- **Packaging** — uv, ruff, pytest, pre-commit, GitHub Actions, Docker

## Architecture
```
Open-Meteo Weather API    Open-Meteo Air Quality API
      ↓                           ↓
  weather_pipeline        air_quality_pipeline
      ↓                    ↓
    extract.py ←──────shared/extract_utils.py──────→ extract.py
      ↓                                               ↓
   transform.py                                   transform.py
      ↓                                               ↓
     load.py ←───────shared/load_utils.py────────→ load.py
      ↓                                               ↓
      └─────────────── platform.duckdb ──────────────┘
                     (multiple schemas:
                      weather, air_quality)
```

## Project Structure
```
data-platform/
├── src/
│   ├── weather_pipeline/       # Weather data pipeline
│   │   ├── config.py           # pipeline-specific settings
│   │   ├── models.py           # weather data models
│   │   ├── extract.py          # Open-Meteo API calls
│   │   ├── transform.py        # weather data cleaning
│   │   ├── load.py             # DuckDB weather writes
│   │   └── pipeline.py         # weather orchestrator
│   ├── air_quality_pipeline/   # Air quality data pipeline
│   │   ├── config.py           # pipeline-specific settings
│   │   ├── models.py           # air quality data models
│   │   ├── extract.py          # Open-Meteo Air Quality API calls
│   │   ├── transform.py        # air quality data cleaning
│   │   ├── load.py             # DuckDB air quality writes
│   │   └── pipeline.py         # air quality orchestrator
│   └── shared/                 # Shared utilities
│       ├── cities.py           # city definitions
│       ├── extract_utils.py    # common extraction patterns
│       ├── load_utils.py       # common loading patterns
│       ├── models.py           # base models
│       └── config_base.py      # base configuration
├── tests/                      # unit tests (mirrors src/)
├── data/                       # DuckDB database file (git ignored)
├── Dockerfile
├── Makefile
└── pyproject.toml
```

---

## Great Expectations — Overview

```
extract → transform → load → DuckDB
                                ↓
                    Great Expectations validates
                    the data already in DuckDB
```

**What is validate:**
- No null cities
- Temperature within realistic range (-60°C to +60°C)
- Humidity between 0-100%
- PM2.5 values non-negative
- Row counts per city are as expected
- No duplicate `(city, timestamp)` rows

**Where GE code lives:**
```
src/
├── shared/
│   └── expectations/          ← shared GE context
├── weather_pipeline/
│   └── validate.py            ← weather-specific expectations
└── air_quality_pipeline/
    └── validate.py            ← air quality-specific expectations
```


## Getting Started

### Prerequisites
- [uv](https://docs.astral.sh/uv/) installed
- Python 3.13
- Docker (optional)

### Local Setup
```bash
git clone <repo>
cd data-platform
make install
cp .env.example .env
```

### Configure Cities
Edit `.env`:
```bash
CITIES=["Helsinki","Tampere","Pori","Turku","Oulu","Rovaniemi","Jyväskylä","Espoo","Vantaa","Lahti"]
```

### Run the Pipelines
```bash
# Run weather pipeline
make run

# Run air quality pipeline
python -m air_quality_pipeline

# Run both pipelines
make run && python -m air_quality_pipeline
```

### Query the Data

#### Weather Data
```bash
uv run python -c "
import duckdb
conn = duckdb.connect('data/platform.duckdb')
rows = conn.execute('''
    SELECT city, date, AVG(temperature_c) as avg_temp, AVG(humidity_pct) as avg_humidity
    FROM weather.weather_records
    GROUP BY city, date
    ORDER BY city
''').fetchall()
for row in rows:
    print(row)
"
```

#### Air Quality Data
```bash
uv run python -c "
import duckdb
conn = duckdb.connect('data/platform.duckdb')
rows = conn.execute('''
    SELECT city, date,
           AVG(pm2_5) as avg_pm2_5,
           AVG(pm10) as avg_pm10,
           AVG(nitrogen_dioxide) as avg_no2
    FROM air_quality.air_quality_records
    GROUP BY city, date
    ORDER BY city, date
''').fetchall()
for row in rows:
    print(row)
"
```

#### Cross-Source Analysis
```bash
uv run python -c "
import duckdb
conn = duckdb.connect('data/platform.duckdb')
rows = conn.execute('''
    SELECT
        w.city,
        w.date,
        AVG(w.temperature_c) as avg_temp,
        AVG(aq.value) as avg_pm25
    FROM weather.weather_records w
    JOIN air_quality.air_quality_records aq
        ON w.city = aq.city AND w.date = aq.date
    WHERE aq.parameter = 'pm25'
    GROUP BY w.city, w.date
    ORDER BY w.city, w.date
''').fetchall()
for row in rows:
    print(row)
"
```

## Docker

### Build
```bash
docker build -t data-platform .
```

### Run Weather Pipeline (default)
Pass cities as JSON and mount local `data/` folder so the DuckDB file persists
after the container exits:
```bash
docker run \
  -e CITIES='["Helsinki","Tampere","Pori","Turku","Oulu","Rovaniemi","Jyväskylä","Espoo","Vantaa","Lahti"]' \
  -v $(pwd)/data:/app/data \
  data-platform
```

### Run Air Quality Pipeline
Set the PIPELINE environment variable:
```bash
docker run \
  -e PIPELINE=air_quality_pipeline \
  -e CITIES='["Helsinki","Tampere","Pori","Turku","Oulu","Rovaniemi","Jyväskylä","Espoo","Vantaa","Lahti"]' \
  -v $(pwd)/data:/app/data \
  data-platform
```

### Query Data After Docker Run
The DuckDB file is written to your local `data/` folder via the volume mount:
```bash
uv run python -c "
import duckdb
conn = duckdb.connect('data/platform.duckdb')
# Check weather data
weather_rows = conn.execute('SELECT city, COUNT(*) as rows FROM weather.weather_records GROUP BY city').fetchall()
print('Weather data:')
for row in weather_rows:
    print(row)

# Check air quality data
air_rows = conn.execute('SELECT city, COUNT(*) as rows FROM air_quality.air_quality_records GROUP BY city').fetchall()
print('Air quality data:')
for row in air_rows:
    print(row)
"
```

### Go Inside the Container (for debugging)
```bash
docker run -it --entrypoint /bin/bash data-platform
# Run weather pipeline
uv run python -m weather_pipeline
# Run air quality pipeline
uv run python -m air_quality_pipeline
```

## Development

### Run Tests
```bash
make test
```

### Lint & Format
```bash
make lint
make format
make fix
```

### Add a Dependency
```bash
uv add <package>              # runtime
uv add --dev <package>        # dev only
# always commit pyproject.toml and uv.lock together
```

## Changelog
See [CHANGELOG.md](CHANGELOG.md) for version history.

## Future Roadmap

### Data Quality
- [ ] Great Expectations / Soda Core data quality checks
- [ ] Schema validation on raw API responses
- [ ] Alerting on missing or anomalous data

### Storage & Modelling
- [ ] Swap DuckDB → Snowflake / Databricks
- [ ] dbt models on top of `weather_records` (staging, marts)
- [ ] Slowly Changing Dimensions (SCD Type 2) for city metadata
- [ ] Data partitioning by date

### Orchestration
- [ ] Airflow DAG to schedule pipeline runs
- [ ] Backfill historical weather data
- [ ] Retry and alerting strategies in Airflow

### Observability
- [ ] Structured logging to a log aggregator (Datadog, CloudWatch)
- [ ] Pipeline metrics (rows processed, duration, error rate)
- [ ] Data lineage tracking

### Infrastructure
- [ ] Docker Compose for local full-stack development
- [ ] Kubernetes deployment manifests
- [ ] Terraform for cloud infrastructure
- [ ] CI/CD deployment pipeline (not just testing)

### New Sources
- [ ] Add forecast vs actuals comparison
- [ ] REST API to serve weather and air quality data
- [ ] Cross-source analysis (weather + air quality correlations)

### ML
- [ ] Weather anomaly detection
- [ ] Temperature forecasting model
- [ ] Feature store integration
