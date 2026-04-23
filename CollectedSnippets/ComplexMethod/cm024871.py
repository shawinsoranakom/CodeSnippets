def test_explicitly_included() -> None:
    """Test if an entity is explicitly included."""
    conf = {
        "include": {
            "domains": ["light"],
            "entity_globs": ["sensor.kitchen_*"],
            "entities": ["switch.kitchen"],
        },
        "exclude": {
            "domains": ["cover"],
            "entity_globs": ["sensor.weather_*"],
            "entities": ["light.kitchen"],
        },
    }
    filt: EntityFilter = INCLUDE_EXCLUDE_FILTER_SCHEMA(conf)
    assert not filt.explicitly_included("light.any")
    assert not filt.explicitly_included("switch.other")
    assert filt.explicitly_included("sensor.kitchen_4")
    assert filt.explicitly_included("switch.kitchen")

    assert not filt.explicitly_excluded("light.any")
    assert not filt.explicitly_excluded("switch.other")
    assert filt.explicitly_excluded("sensor.weather_5")
    assert filt.explicitly_excluded("light.kitchen")