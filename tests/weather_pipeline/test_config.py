"""Unit tests for the WeatherSettings class in weather_pipeline.config."""

from shared.cities import FINNISH_CITIES, get_cities
from weather_pipeline.config import WeatherSettings, settings


def test_default_cities():
    s = WeatherSettings()
    assert isinstance(s.cities, list)
    assert len(s.cities) > 0


def test_default_api_url():
    s = WeatherSettings()
    assert s.api_base_url.startswith("https://")


def test_cities_from_env(monkeypatch):
    monkeypatch.setenv("WEATHER_CITIES", '["Oslo","Berlin"]')
    s = WeatherSettings()
    assert s.cities == ["Oslo", "Berlin"]


def test_shared_settings_instance():
    assert settings is not None
    assert isinstance(settings.cities, list)


def test_default_city_scope():
    s = WeatherSettings()
    assert s.city_scope == "finland"


def test_cities_list_uses_finnish_by_default():
    s = WeatherSettings()
    assert s.cities_list == FINNISH_CITIES


def test_cities_list_uses_scope(monkeypatch):
    monkeypatch.setenv("WEATHER_CITY_SCOPE", "nordic")
    s = WeatherSettings()
    assert s.cities_list == get_cities("nordic")


def test_cities_list_finland_scope(monkeypatch):
    monkeypatch.setenv("WEATHER_CITY_SCOPE", "finland")
    s = WeatherSettings()
    assert "Helsinki" in s.cities_list


def test_cities_list_property():
    assert isinstance(settings.cities_list, list)
    assert "Helsinki" in settings.cities_list


def test_db_path_property():
    """Test db_path property returns correct path."""
    s = WeatherSettings()
    assert s.db_path == "data/platform.duckdb"


def test_db_schema_property():
    """Test db_schema property returns correct schema."""
    s = WeatherSettings()
    assert s.db_schema == "weather"
