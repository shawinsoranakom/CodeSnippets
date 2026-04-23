async def test_config_options(hass: HomeAssistant) -> None:
    """Test configuration options."""
    count_start = len(hass.states.async_entity_ids())

    _LOGGER.debug("ENTITIES @ start: %s", hass.states.async_entity_ids())

    assert await async_setup_component(
        hass,
        DOMAIN,
        {
            DOMAIN: {
                "test_1": None,
                "test_2": {"name": "Hello World", "icon": "mdi:work"},
            }
        },
    )

    _LOGGER.debug("ENTITIES: %s", hass.states.async_entity_ids())

    assert count_start + 2 == len(hass.states.async_entity_ids())

    state_1 = hass.states.get("input_button.test_1")
    state_2 = hass.states.get("input_button.test_2")

    assert state_1 is not None
    assert state_2 is not None

    assert state_1.state == STATE_UNKNOWN
    assert ATTR_ICON not in state_1.attributes
    assert ATTR_FRIENDLY_NAME not in state_1.attributes

    assert state_2.state == STATE_UNKNOWN
    assert state_2.attributes.get(ATTR_FRIENDLY_NAME) == "Hello World"
    assert state_2.attributes.get(ATTR_ICON) == "mdi:work"