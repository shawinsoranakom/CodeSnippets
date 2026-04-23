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
                CONF_DURATION: 10,
            },
            "test_3": None,
        }
    }

    assert await async_setup_component(hass, "timer", config)
    await hass.async_block_till_done()

    assert count_start + 3 == len(hass.states.async_entity_ids())
    await hass.async_block_till_done()

    state_1 = hass.states.get("timer.test_1")
    state_2 = hass.states.get("timer.test_2")
    state_3 = hass.states.get("timer.test_3")

    assert state_1 is not None
    assert state_2 is not None
    assert state_3 is not None

    assert state_1.state == STATUS_IDLE
    assert state_1.attributes == {
        ATTR_EDITABLE: False,
        ATTR_DURATION: "0:00:00",
    }

    assert state_2.state == STATUS_IDLE
    assert state_2.attributes == {
        ATTR_DURATION: "0:00:10",
        ATTR_EDITABLE: False,
        ATTR_FRIENDLY_NAME: "Hello World",
        ATTR_ICON: "mdi:work",
    }

    assert state_3.state == STATUS_IDLE
    assert state_3.attributes == {
        ATTR_DURATION: str(cv.time_period(DEFAULT_DURATION)),
        ATTR_EDITABLE: False,
    }