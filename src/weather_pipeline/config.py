"""Configuration settings for the weather data application."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
    )

    cities: list[str] = ["London", "Helsinki", "Tokyo"]
    api_base_url: str = "https://api.open-meteo.com/v1"
    db_path: str = "data/weather.duckdb"
    log_level: str = "INFO"

    @property
    def cities_list(self) -> list[str]:
        return [c.strip() for c in self.cities]


# single shared instance — import this everywhere
settings = Settings()
