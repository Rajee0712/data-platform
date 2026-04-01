"""Tests for air_quality_pipeline.config module."""

from air_quality_pipeline.config import AirQualitySettings


def test_settings_defaults():
    """Test that AirQualitySettings has sensible defaults."""
    settings = AirQualitySettings()
    assert settings.api_base_url == "https://air-quality-api.open-meteo.com/v1"
    assert settings.db_path == "data/platform.duckdb"
    assert settings.log_level == "INFO"
    assert settings.city_scope == "finland"


def test_cities_list_property_finland():
    """Test cities_list returns default cities for finland scope."""
    settings = AirQualitySettings(city_scope="finland")
    cities = settings.cities_list
    assert isinstance(cities, list)
    assert len(cities) > 0
    assert "Helsinki" in cities


def test_cities_list_property_other_scope(monkeypatch):
    """Test cities_list uses get_cities for non-finland scopes."""
    mock_cities = ["Stockholm", "Oslo", "Copenhagen"]

    def mock_get_cities(scope):
        return mock_cities

    monkeypatch.setattr("air_quality_pipeline.config.get_cities", mock_get_cities)

    settings = AirQualitySettings(city_scope="nordic")
    assert settings.cities_list == mock_cities
