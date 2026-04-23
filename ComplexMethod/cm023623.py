def test_condition_class() -> None:
    """Test condition class."""

    def get_condition(index: int) -> str:
        """Return condition given index."""
        return [k for k, v in CONDITION_CLASSES.items() if index in v][0]

    # SMHI definitions as follows, see
    # http://opendata.smhi.se/apidocs/metfcst/parameters.html

    # 1. Clear sky
    assert get_condition(1) == "sunny"
    # 2. Nearly clear sky
    assert get_condition(2) == "sunny"
    # 3. Variable cloudiness
    assert get_condition(3) == "partlycloudy"
    # 4. Halfclear sky
    assert get_condition(4) == "partlycloudy"
    # 5. Cloudy sky
    assert get_condition(5) == "cloudy"
    # 6. Overcast
    assert get_condition(6) == "cloudy"
    # 7. Fog
    assert get_condition(7) == "fog"
    # 8. Light rain showers
    assert get_condition(8) == "rainy"
    # 9. Moderate rain showers
    assert get_condition(9) == "rainy"
    # 18. Light rain
    assert get_condition(18) == "rainy"
    # 19. Moderate rain
    assert get_condition(19) == "rainy"
    # 10. Heavy rain showers
    assert get_condition(10) == "pouring"
    # 20. Heavy rain
    assert get_condition(20) == "pouring"
    # 21. Thunder
    assert get_condition(21) == "lightning"
    # 11. Thunderstorm
    assert get_condition(11) == "lightning-rainy"
    # 15. Light snow showers
    assert get_condition(15) == "snowy"
    # 16. Moderate snow showers
    assert get_condition(16) == "snowy"
    # 17. Heavy snow showers
    assert get_condition(17) == "snowy"
    # 25. Light snowfall
    assert get_condition(25) == "snowy"
    # 26. Moderate snowfall
    assert get_condition(26) == "snowy"
    # 27. Heavy snowfall
    assert get_condition(27) == "snowy"
    # 12. Light sleet showers
    assert get_condition(12) == "snowy-rainy"
    # 13. Moderate sleet showers
    assert get_condition(13) == "snowy-rainy"
    # 14. Heavy sleet showers
    assert get_condition(14) == "snowy-rainy"
    # 22. Light sleet
    assert get_condition(22) == "snowy-rainy"
    # 23. Moderate sleet
    assert get_condition(23) == "snowy-rainy"
    # 24. Heavy sleet
    assert get_condition(24) == "snowy-rainy"