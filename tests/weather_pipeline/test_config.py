"""
Unit tests for the Settings class in weather_pipeline.config.
"""

from weather_pipeline.config import Settings, settings


def test_default_cities():
    s = Settings()
    assert isinstance(s.cities, list)
    assert len(s.cities) > 0


def test_default_api_url():
    s = Settings()
    assert s.api_base_url.startswith("https://")


def test_cities_from_env(monkeypatch):
    monkeypatch.setenv("CITIES", '["Oslo","Berlin"]')
    s = Settings()
    assert s.cities == ["Oslo", "Berlin"]


def test_shared_settings_instance():
    assert settings is not None
    assert isinstance(settings.cities, list)


def test_cities_list_property():
    assert isinstance(settings.cities_list, list)
    assert "Helsinki" in settings.cities_list
