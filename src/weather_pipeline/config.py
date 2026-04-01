"""Configuration settings for the weather data application."""

from pydantic_settings import SettingsConfigDict

from shared.config_base import PipelineSettings


class WeatherSettings(PipelineSettings):
    """Weather pipeline specific configuration settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        env_prefix="WEATHER_",
        extra="ignore",
    )

    @property
    def api_base_url(self) -> str:
        return "https://api.open-meteo.com/v1"

    @property
    def db_path(self) -> str:
        return "data/platform.duckdb"

    @property
    def db_schema(self) -> str:
        return "weather"


# single shared instance — import this everywhere
settings = WeatherSettings()
