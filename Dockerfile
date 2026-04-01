FROM python:3.13-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files first (better layer caching)
COPY pyproject.toml uv.lock ./

# Install dependencies only (no dev deps in production)
RUN uv sync --no-dev --frozen --no-install-project

# Copy application code
COPY src/ ./src/

# Install project
RUN uv pip install -e .

# Mount data to local directory
VOLUME /app/data

# Set environment variable for which pipeline to run (default: weather)
ENV PIPELINE=weather_pipeline

# Run the specified pipeline
CMD ["sh", "-c", "uv run python -m $PIPELINE"]
