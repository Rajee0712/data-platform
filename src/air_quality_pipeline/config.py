"""Configuration settings for the air quality data application."""

from pydantic_settings import SettingsConfigDict

from shared.config_base import PipelineSettings


class AirQualitySettings(PipelineSettings):
    """Air quality pipeline specific configuration settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        env_prefix="AIR_QUALITY_",
        extra="ignore",
    )

    @property
    def api_base_url(self) -> str:
        return "https://air-quality-api.open-meteo.com/v1"

    @property
    def db_path(self) -> str:
        return "data/platform.duckdb"

    @property
    def db_schema(self) -> str:
        return "air_quality"


# single shared instance — import this everywhere
settings = AirQualitySettings()
