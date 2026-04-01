"""City definitions organised by country/region."""

FINNISH_CITIES = [
    "Helsinki",
    "Espoo",
    "Tampere",
    "Turku",
    "Oulu",
    "Rovaniemi",
    "Jyväskylä",
    "Lahti",
    "Pori",
    "Vantaa",
]

NORDIC_CITIES = [
    "Stockholm",
    "Gothenburg",
    "Malmö",
    "Oslo",
    "Bergen",
    "Trondheim",
    "Copenhagen",
    "Aarhus",
    "Reykjavik",
    *FINNISH_CITIES,
]

EUROPEAN_CITIES = [
    "London",
    "Paris",
    "Berlin",
    "Madrid",
    "Rome",
    "Amsterdam",
    "Vienna",
    "Warsaw",
    "Prague",
    "Budapest",
    "Lisbon",
    "Athens",
    *NORDIC_CITIES,
]

WORLD_CITIES = [
    "Tokyo",
    "Beijing",
    "Delhi",
    "Mumbai",
    "New York",
    "Los Angeles",
    "São Paulo",
    "Cairo",
    "Lagos",
    "Nairobi",
    "Sydney",
    "Melbourne",
    *EUROPEAN_CITIES,
]

CITY_SCOPES = {
    "finland": FINNISH_CITIES,
    "nordic": NORDIC_CITIES,
    "europe": EUROPEAN_CITIES,
    "world": WORLD_CITIES,
}


def get_cities(scope: str = "finland") -> list[str]:
    """Get cities by scope. Defaults to Finnish cities."""
    if scope not in CITY_SCOPES:
        raise ValueError(
            f"Unknown scope: {scope}. Choose from {list(CITY_SCOPES.keys())}"
        )
    return CITY_SCOPES[scope]
