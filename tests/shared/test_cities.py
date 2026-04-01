"""Unit tests for shared cities."""

import pytest

from shared.cities import (
    CITY_SCOPES,
    EUROPEAN_CITIES,
    FINNISH_CITIES,
    NORDIC_CITIES,
    WORLD_CITIES,
    get_cities,
)


def test_finnish_cities_is_list():
    assert isinstance(FINNISH_CITIES, list)


def test_finnish_cities_not_empty():
    assert len(FINNISH_CITIES) > 0


def test_finnish_cities_are_strings():
    assert all(isinstance(city, str) for city in FINNISH_CITIES)


def test_helsinki_in_cities():
    assert "Helsinki" in FINNISH_CITIES


def test_nordic_includes_finnish():
    assert all(city in NORDIC_CITIES for city in FINNISH_CITIES)


def test_european_includes_nordic():
    assert all(city in EUROPEAN_CITIES for city in NORDIC_CITIES)


def test_world_includes_european():
    assert all(city in WORLD_CITIES for city in EUROPEAN_CITIES)


def test_get_cities_finland():
    assert get_cities("finland") == FINNISH_CITIES


def test_get_cities_nordic():
    assert get_cities("nordic") == NORDIC_CITIES


def test_get_cities_europe():
    assert get_cities("europe") == EUROPEAN_CITIES


def test_get_cities_world():
    assert get_cities("world") == WORLD_CITIES


def test_get_cities_invalid_scope():
    with pytest.raises(ValueError, match="Unknown scope"):
        get_cities("mars")


def test_all_scopes_present():
    assert set(CITY_SCOPES.keys()) == {"finland", "nordic", "europe", "world"}
