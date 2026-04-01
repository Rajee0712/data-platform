"""Configuration settings for the air quality data application."""

from pydantic_settings import BaseSettings, SettingsConfigDict

from shared.cities import FINNISH_CITIES, get_cities


class AirQualitySettings(BaseSettings):
    """Application configuration settings loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        env_prefix="AIR_QUALITY_",
        extra="ignore",
    )

    cities: list[str] = FINNISH_CITIES
    city_scope: str = "finland"
    api_base_url: str = "https://air-quality-api.open-meteo.com/v1"
    db_path: str = "data/platform.duckdb"
    log_level: str = "INFO"

    @property
    def cities_list(self) -> list[str]:
        if self.city_scope != "finland":
            return get_cities(self.city_scope)
        return self.cities


settings = AirQualitySettings()
