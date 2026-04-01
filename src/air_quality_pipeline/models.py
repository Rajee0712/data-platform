"""Data models for the air quality data application."""

from shared.models import BaseRawResponse, BaseRecord

AIR_QUALITY_VARIABLES = [
    "pm2_5",
    "pm10",
    "carbon_monoxide",
    "nitrogen_dioxide",
    "ozone",
]


class RawAirQualityResponse(BaseRawResponse):
    """Raw response from Open-Meteo air quality API."""

    latitude: float
    longitude: float
    timezone: str
    hourly_units: dict[str, str]
    hourly: dict[str, list]

    def get_data_field(self) -> str:
        """Return the field name that contains the data array."""
        return "hourly"


class AirQualityRecord(BaseRecord):
    """A single cleaned hourly air quality observation — one row in DuckDB."""

    pm2_5: float | None = None
    pm10: float | None = None
    carbon_monoxide: float | None = None
    nitrogen_dioxide: float | None = None
    ozone: float | None = None

    def get_primary_key_fields(self) -> list[str]:
        """Return primary key fields for database upserts."""
        return ["city", "timestamp"]
