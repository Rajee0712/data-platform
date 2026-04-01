"""Data models for the air quality data application."""

from datetime import UTC, date, datetime

from pydantic import BaseModel, Field


class CityCoordinates(BaseModel):
    """Lat/lon for a city resolved before API call."""

    city: str
    latitude: float
    longitude: float


class RawAirQualityResponse(BaseModel):
    """Raw response from OpenAQ API — mirrors their JSON structure."""

    results: list[dict]


class AirQualityRecord(BaseModel):
    """A single cleaned, typed air quality measurement — one row in DuckDB."""

    city: str
    timestamp: datetime
    date: date
    parameter: str = Field(description="Pollutant parameter (pm25, pm10, no2, etc.)")
    value: float = Field(description="Measured value")
    unit: str = Field(description="Unit of measurement")
    coordinates_latitude: float = Field(description="Measurement location latitude")
    coordinates_longitude: float = Field(description="Measurement location longitude")
    ingested_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When this record was written to the DB",
    )
