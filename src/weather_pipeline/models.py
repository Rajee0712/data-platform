"""Data models for the weather data application."""

from pydantic import Field

from shared.models import BaseRawResponse, BaseRecord


class RawWeatherResponse(BaseRawResponse):
    """Raw response from Open-Meteo API — mirrors their JSON structure."""

    latitude: float
    longitude: float
    timezone: str
    hourly_units: dict[str, str]
    hourly: dict[str, list]

    def get_data_field(self) -> str:
        """Return the field name that contains the data array."""
        return "hourly"


class WeatherRecord(BaseRecord):
    """A single cleaned, typed hourly weather observation — one row in DuckDB."""

    temperature_c: float = Field(description="Air temperature at 2m in Celsius")
    humidity_pct: float = Field(description="Relative humidity at 2m in %")
    windspeed_kmh: float = Field(description="Wind speed at 10m in km/h")
    precipitation_mm: float = Field(description="Precipitation in mm")

    def get_primary_key_fields(self) -> list[str]:
        """Return primary key fields for database upserts."""
        return ["city", "timestamp"]
