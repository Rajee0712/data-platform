"""Data models for the air quality data application."""

from datetime import UTC, date, datetime

from pydantic import BaseModel, Field

AIR_QUALITY_VARIABLES = [
    "pm2_5",
    "pm10",
    "carbon_monoxide",
    "nitrogen_dioxide",
    "ozone",
]


class CityCoordinates(BaseModel):
    """Lat/lon for a city resolved before API call."""

    city: str
    latitude: float
    longitude: float


class RawAirQualityResponse(BaseModel):
    """Raw response from Open-Meteo air quality API."""

    latitude: float
    longitude: float
    timezone: str
    hourly_units: dict[str, str]
    hourly: dict[str, list]


class AirQualityRecord(BaseModel):
    """A single cleaned hourly air quality observation — one row in DuckDB."""

    city: str
    timestamp: datetime
    date: date
    pm2_5: float | None = None
    pm10: float | None = None
    carbon_monoxide: float | None = None
    nitrogen_dioxide: float | None = None
    ozone: float | None = None
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
