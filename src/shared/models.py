"""Shared data models for all pipelines."""

from datetime import UTC, date, datetime

from pydantic import BaseModel, Field


class CityCoordinates(BaseModel):
    """Lat/lon for a city resolved before API call."""

    city: str
    latitude: float
    longitude: float


class BaseRawResponse(BaseModel):
    """Base class for all API responses."""

    def get_data_field(self) -> str:
        """Override in subclasses to specify which field contains the data array."""
        raise NotImplementedError


class BaseRecord(BaseModel):
    """Base class for all data records with common fields."""

    city: str
    timestamp: datetime
    date: date
    ingested_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When this record was written to the DB",
    )

    def get_primary_key_fields(self) -> list[str]:
        """Override in subclasses to specify primary key fields for upserts."""
        return ["city", "timestamp"]
