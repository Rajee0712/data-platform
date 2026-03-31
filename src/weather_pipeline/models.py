"""Data models for the weather data application."""

from datetime import UTC, date, datetime

from pydantic import BaseModel, Field


class CityCoordinates(BaseModel):
    """Lat/lon for a city resolved before API call."""

    city: str
    latitude: float
    longitude: float


class RawWeatherResponse(BaseModel):
    """Raw response from Open-Meteo API — mirrors their JSON structure."""

    latitude: float
    longitude: float
    timezone: str
    hourly_units: dict[str, str]
    hourly: dict[str, list]


class WeatherRecord(BaseModel):
    """A single cleaned, typed hourly weather observation — one row in DuckDB."""

    city: str
    timestamp: datetime
    date: date
    temperature_c: float = Field(description="Air temperature at 2m in Celsius")
    humidity_pct: float = Field(description="Relative humidity at 2m in %")
    windspeed_kmh: float = Field(description="Wind speed at 10m in km/h")
    precipitation_mm: float = Field(description="Precipitation in mm")
    ingested_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When this record was written to the DB",
    )
