def test_async_get_entities_cached(hass: HomeAssistant) -> None:
    """Test async_get_entities is cached."""
    config = MockConfig()

    hass.states.async_set("light.ceiling_lights", "off")
    hass.states.async_set("light.bed_light", "off")
    hass.states.async_set("not_supported.not_supported", "off")

    google_entities = helpers.async_get_entities(hass, config)
    assert len(google_entities) == 2
    assert config.is_supported_cache == {
        "light.bed_light": (None, True),
        "light.ceiling_lights": (None, True),
        "not_supported.not_supported": (None, False),
    }

    with patch(
        "homeassistant.components.google_assistant.helpers.GoogleEntity.traits",
        return_value=RuntimeError("Should not be called"),
    ):
        google_entities = helpers.async_get_entities(hass, config)

    assert len(google_entities) == 2
    assert config.is_supported_cache == {
        "light.bed_light": (None, True),
        "light.ceiling_lights": (None, True),
        "not_supported.not_supported": (None, False),
    }

    hass.states.async_set("light.new", "on")
    google_entities = helpers.async_get_entities(hass, config)

    assert len(google_entities) == 3
    assert config.is_supported_cache == {
        "light.bed_light": (None, True),
        "light.new": (None, True),
        "light.ceiling_lights": (None, True),
        "not_supported.not_supported": (None, False),
    }

    hass.states.async_set("light.new", "on", {"supported_features": 1})
    google_entities = helpers.async_get_entities(hass, config)

    assert len(google_entities) == 3
    assert config.is_supported_cache == {
        "light.bed_light": (None, True),
        "light.new": (1, True),
        "light.ceiling_lights": (None, True),
        "not_supported.not_supported": (None, False),
    }