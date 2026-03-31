# Weather Pipeline

[![Coverage](https://codecov.io/gh/Rajee0712/data-platform/branch/main/graph/badge.svg)](https://codecov.io/gh/Rajee0712/data-platform)

A production-grade ELT pipeline that fetches hourly weather data from the
[Open-Meteo API](https://open-meteo.com/) for a set of cities and loads it into DuckDB.

## Stack
- **Extract** — Open-Meteo API via httpx + tenacity retries
- **Transform** — Pydantic models for typed, validated records
- **Load** — DuckDB with idempotent upserts
- **Packaging** — uv, ruff, pytest, pre-commit, GitHub Actions, Docker

## Project Structure
```
weather-pipeline/
├── weather_pipeline/       # Python package
│   ├── config.py           # settings via pydantic-settings
│   ├── models.py           # Pydantic data models
│   ├── extract.py          # API calls
│   ├── transform.py        # cleaning and typing
│   ├── load.py             # DuckDB writes
│   └── pipeline.py         # orchestrator
├── tests/                  # unit tests
├── data/                   # DuckDB database (git ignored)
├── Dockerfile
├── Makefile
└── pyproject.toml
```

## Getting Started

### Prerequisites
- [uv](https://docs.astral.sh/uv/) installed
- Python 3.13
- Docker (optional)

### Local Setup
```bash
git clone <repo>
cd weather-pipeline
make install
cp .env.example .env
```

### Configure Cities
Edit `.env`:
```bash
CITIES=["Helsinki","Tampere","Pori","Turku","Oulu","Rovaniemi","Jyväskylä","Espoo","Vantaa","Lahti"]
```

### Run the Pipeline
```bash
make run
```

### Query the Data
```bash
uv run python -c "
import duckdb
conn = duckdb.connect('data/weather.duckdb')
rows = conn.execute('''
    SELECT city, date, AVG(temperature_c) as avg_temp, AVG(humidity_pct) as avg_humidity
    FROM weather_records
    GROUP BY city, date
    ORDER BY city
''').fetchall()
for row in rows:
    print(row)
"
```

## Docker

### Build
```bash
docker build -t weather-pipeline .
```

### Run
Pass cities as JSON and mount local `data/` folder so the DuckDB file persists
after the container exits:
```bash
docker run \
  -e CITIES='["Helsinki","Tampere","Pori","Turku","Oulu","Rovaniemi","Jyväskylä","Espoo","Vantaa","Lahti"]' \
  -v $(pwd)/data:/app/data \
  weather-pipeline
```

### Query Data After Docker Run
The DuckDB file is written to your local `data/` folder via the volume mount:
```bash
uv run python -c "
import duckdb
conn = duckdb.connect('data/weather.duckdb')
rows = conn.execute('SELECT city, COUNT(*) as rows FROM weather_records GROUP BY city').fetchall()
for row in rows:
    print(row)
"
```

### Go Inside the Container (for debugging)
```bash
docker run -it --entrypoint /bin/bash weather-pipeline
uv run python -m weather_pipeline.pipeline
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
- [ ] Add air quality pipeline (second source system)
- [ ] Add forecast vs actuals comparison
- [ ] REST API to serve weather data

### ML
- [ ] Weather anomaly detection
- [ ] Temperature forecasting model
- [ ] Feature store integration
