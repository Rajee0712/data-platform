"""Shared configuration base for all pipelines."""

from pydantic_settings import BaseSettings, SettingsConfigDict

from shared.cities import FINNISH_CITIES, get_cities


class PipelineSettings(BaseSettings):
    """Base configuration settings for all pipelines."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
    )

    # Common fields
    cities: list[str] = FINNISH_CITIES
    city_scope: str = "finland"
    log_level: str = "INFO"

    @property
    def cities_list(self) -> list[str]:
        """Get cities list based on scope configuration."""
        if self.city_scope != "finland":
            return get_cities(self.city_scope)
        return self.cities

    # Abstract properties that subclasses must override
    @property
    def api_base_url(self) -> str:
        raise NotImplementedError("Subclasses must define api_base_url")

    @property
    def db_path(self) -> str:
        raise NotImplementedError("Subclasses must define db_path")
