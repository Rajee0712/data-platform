FROM python:3.13-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files first (better layer caching)
COPY pyproject.toml uv.lock ./

# Install dependencies only (no dev deps in production)
RUN uv sync --no-dev --frozen

# Copy application code
COPY weather_pipeline/ ./weather_pipeline/

# Mount data to local directory
VOLUME /app/data

# Run the pipeline
CMD ["uv", "run", "python", "-m", "weather_pipeline.pipeline"]
