async def test_config_options(hass: HomeAssistant) -> None:
    """Test configuration options."""
    count_start = len(hass.states.async_entity_ids())

    _LOGGER.debug("ENTITIES @ start: %s", hass.states.async_entity_ids())

    config = {
        DOMAIN: {
            "test_1": {},
            "test_2": {
                CONF_NAME: "Hello World",
                CONF_ICON: "mdi:work",
                CONF_INITIAL: 10,
                CONF_RESTORE: False,
                CONF_STEP: 5,
            },
            "test_3": None,
        }
    }

    assert await async_setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done()

    _LOGGER.debug("ENTITIES: %s", hass.states.async_entity_ids())

    assert count_start + 3 == len(hass.states.async_entity_ids())
    await hass.async_block_till_done()

    state_1 = hass.states.get("counter.test_1")
    state_2 = hass.states.get("counter.test_2")
    state_3 = hass.states.get("counter.test_3")

    assert state_1 is not None
    assert state_2 is not None
    assert state_3 is not None

    assert int(state_1.state) == 0
    assert ATTR_ICON not in state_1.attributes
    assert ATTR_FRIENDLY_NAME not in state_1.attributes

    assert int(state_2.state) == 10
    assert state_2.attributes.get(ATTR_FRIENDLY_NAME) == "Hello World"
    assert state_2.attributes.get(ATTR_ICON) == "mdi:work"

    assert state_3.attributes.get(ATTR_INITIAL) == DEFAULT_INITIAL
    assert state_3.attributes.get(ATTR_STEP) == DEFAULT_STEP