async def test_linear_state(hass: HomeAssistant, config: dict[str, Any]) -> None:
    """Test compensation sensor state."""
    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    hass.states.async_set(TEST_SOURCE, 4, {})
    await hass.async_block_till_done()

    state = hass.states.get(TEST_ENTITY_ID)
    assert state is not None

    assert round(float(state.state), config[CONF_PRECISION]) == 5.0

    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == "a"

    coefs = [round(v, 1) for v in state.attributes.get(ATTR_COEFFICIENTS)]
    assert coefs == [1.0, 1.0]

    hass.states.async_set(TEST_SOURCE, "foo", {})
    await hass.async_block_till_done()

    state = hass.states.get(TEST_ENTITY_ID)
    assert state is not None

    assert state.state == STATE_UNKNOWN