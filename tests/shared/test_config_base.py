"""Tests for shared.config_base module."""

import pytest
from pydantic import ValidationError

from shared.cities import FINNISH_CITIES
from shared.config_base import PipelineSettings


class ConcretePipelineSettings(PipelineSettings):
    """Test implementation of PipelineSettings."""

    model_config = PipelineSettings.model_config.copy()
    model_config.update({"env_file": None})  # Don't read .env file in tests

    @property
    def api_base_url(self) -> str:
        return "https://api.test.com/v1"

    @property
    def db_path(self) -> str:
        return "data/test.duckdb"


class IncompletePipelineSettings(PipelineSettings):
    """Incomplete implementation missing abstract properties."""

    model_config = PipelineSettings.model_config.copy()
    model_config.update({"env_file": None})  # Don't read .env file in tests


def test_pipeline_settings_default_values():
    """Test default values in PipelineSettings."""
    settings = ConcretePipelineSettings()

    assert settings.cities == FINNISH_CITIES
    assert settings.city_scope == "finland"
    assert settings.log_level == "INFO"


def test_pipeline_settings_custom_values():
    """Test PipelineSettings with custom values."""
    custom_cities = ["Stockholm", "Oslo", "Copenhagen"]

    settings = ConcretePipelineSettings(
        cities=custom_cities, city_scope="nordic", log_level="DEBUG"
    )

    assert settings.cities == custom_cities
    assert settings.city_scope == "nordic"
    assert settings.log_level == "DEBUG"


def test_pipeline_settings_cities_list_finland_default():
    """Test cities_list property with default finland scope."""
    settings = ConcretePipelineSettings()

    cities_list = settings.cities_list
    assert cities_list == FINNISH_CITIES
    assert "Helsinki" in cities_list
    assert len(cities_list) > 0


def test_pipeline_settings_cities_list_finland_explicit():
    """Test cities_list property with explicit finland scope."""
    custom_cities = ["CustomCity1", "CustomCity2"]

    settings = ConcretePipelineSettings(cities=custom_cities, city_scope="finland")

    # Should use custom cities, not FINNISH_CITIES
    cities_list = settings.cities_list
    assert cities_list == custom_cities


def test_pipeline_settings_cities_list_other_scope(monkeypatch):
    """Test cities_list property with non-finland scope."""
    mock_cities = ["Stockholm", "Oslo", "Copenhagen"]

    def mock_get_cities(scope):
        return mock_cities

    # Patch the get_cities function in the config_base module
    monkeypatch.setattr("shared.config_base.get_cities", mock_get_cities)

    settings = ConcretePipelineSettings(city_scope="nordic")

    cities_list = settings.cities_list
    assert cities_list == mock_cities


def test_pipeline_settings_cities_list_unknown_scope(monkeypatch):
    """Test cities_list property with unknown scope."""

    def mock_get_cities(scope):
        if scope == "unknown":
            return ["UnknownCity1", "UnknownCity2"]
        return []

    monkeypatch.setattr("shared.config_base.get_cities", mock_get_cities)

    settings = ConcretePipelineSettings(city_scope="unknown")

    cities_list = settings.cities_list
    assert cities_list == ["UnknownCity1", "UnknownCity2"]


def test_concrete_implementation_properties():
    """Test concrete implementation provides required properties."""
    settings = ConcretePipelineSettings()

    assert settings.api_base_url == "https://api.test.com/v1"
    assert settings.db_path == "data/test.duckdb"


def test_abstract_properties_not_implemented():
    """Test that abstract properties raise NotImplementedError when not overridden."""
    settings = IncompletePipelineSettings()

    with pytest.raises(
        NotImplementedError, match="Subclasses must define api_base_url"
    ):
        _ = settings.api_base_url

    with pytest.raises(NotImplementedError, match="Subclasses must define db_path"):
        _ = settings.db_path


def test_environment_variable_loading(monkeypatch):
    """Test loading configuration from environment variables."""
    monkeypatch.setenv("CITIES", '["EnvCity1","EnvCity2"]')
    monkeypatch.setenv("CITY_SCOPE", "environment")
    monkeypatch.setenv("LOG_LEVEL", "ERROR")

    settings = ConcretePipelineSettings()

    assert settings.cities == ["EnvCity1", "EnvCity2"]
    assert settings.city_scope == "environment"
    assert settings.log_level == "ERROR"


def test_settings_validation():
    """Test Pydantic validation of settings."""
    # Valid settings
    settings = ConcretePipelineSettings(
        cities=["Valid1", "Valid2"], city_scope="valid", log_level="INFO"
    )
    assert len(settings.cities) == 2

    # Invalid cities type
    with pytest.raises(ValidationError):
        ConcretePipelineSettings(cities="not_a_list")

    # Invalid log level type
    with pytest.raises(ValidationError):
        ConcretePipelineSettings(log_level=123)


def test_settings_model_config():
    """Test that model configuration is properly set."""
    # Test the base class model config (before test overrides)
    base_config = PipelineSettings.model_config
    assert base_config["env_file"] == ".env"
    assert base_config["env_file_encoding"] == "utf-8"
    assert base_config["env_ignore_empty"] is True


def test_inheritance_structure():
    """Test that PipelineSettings properly inherits from BaseSettings."""
    from pydantic_settings import BaseSettings

    assert issubclass(PipelineSettings, BaseSettings)

    settings = ConcretePipelineSettings()
    assert isinstance(settings, BaseSettings)
    assert isinstance(settings, PipelineSettings)


def test_cities_list_caching_behavior():
    """Test that cities_list property behaves consistently."""
    settings = ConcretePipelineSettings()

    # Multiple calls should return the same result
    cities_1 = settings.cities_list
    cities_2 = settings.cities_list

    assert cities_1 == cities_2
    assert cities_1 is cities_1  # Same object reference for FINNISH_CITIES


def test_cities_list_with_empty_custom_cities():
    """Test cities_list with empty custom cities list."""
    settings = ConcretePipelineSettings(cities=[], city_scope="finland")

    cities_list = settings.cities_list
    assert cities_list == []


def test_cities_list_scope_priority(monkeypatch):
    """Test that scope takes priority over cities field when not finland."""
    mock_scope_cities = ["ScopeCity1", "ScopeCity2"]

    def mock_get_cities(scope):
        return mock_scope_cities

    monkeypatch.setattr("shared.config_base.get_cities", mock_get_cities)

    # Even with custom cities, non-finland scope should use get_cities
    settings = ConcretePipelineSettings(
        cities=["CustomCity1", "CustomCity2"], city_scope="nordic"
    )

    cities_list = settings.cities_list
    assert cities_list == mock_scope_cities  # Should use scope, not custom cities


def test_multiple_settings_instances():
    """Test that multiple settings instances work independently."""
    settings1 = ConcretePipelineSettings(cities=["City1"], city_scope="scope1")
    settings2 = ConcretePipelineSettings(cities=["City2"], city_scope="scope2")

    assert settings1.cities == ["City1"]
    assert settings2.cities == ["City2"]
    assert settings1.city_scope == "scope1"
    assert settings2.city_scope == "scope2"


def test_settings_repr_and_str():
    """Test string representations of settings."""
    settings = ConcretePipelineSettings(city_scope="test")

    # Should not raise exceptions
    repr_str = repr(settings)
    str_str = str(settings)

    assert "ConcretePipelineSettings" in repr_str
    assert isinstance(str_str, str)


def test_get_cities_import():
    """Test that get_cities is properly imported and available."""
    from shared.config_base import get_cities

    # This should not raise an ImportError
    assert callable(get_cities)


def test_finnish_cities_import():
    """Test that FINNISH_CITIES is properly imported and available."""
    from shared.config_base import FINNISH_CITIES

    # This should not raise an ImportError
    assert isinstance(FINNISH_CITIES, list)
    assert len(FINNISH_CITIES) > 0
    assert "Helsinki" in FINNISH_CITIES
