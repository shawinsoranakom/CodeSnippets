async def test_attributes(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test attributes."""
    await mqtt_mock_entry()

    state = hass.states.get("fan.test")
    assert state.state == STATE_UNKNOWN

    await common.async_turn_on(hass, "fan.test")
    state = hass.states.get("fan.test")
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_ASSUMED_STATE)
    assert state.attributes.get(fan.ATTR_OSCILLATING) is None
    assert state.attributes.get(fan.ATTR_DIRECTION) is None

    await common.async_turn_off(hass, "fan.test")
    state = hass.states.get("fan.test")
    assert state.state == STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)
    assert state.attributes.get(fan.ATTR_OSCILLATING) is None
    assert state.attributes.get(fan.ATTR_DIRECTION) is None

    await common.async_oscillate(hass, "fan.test", True)
    state = hass.states.get("fan.test")
    assert state.state == STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)
    assert state.attributes.get(fan.ATTR_OSCILLATING) is True
    assert state.attributes.get(fan.ATTR_DIRECTION) is None

    await common.async_set_direction(hass, "fan.test", "reverse")
    state = hass.states.get("fan.test")
    assert state.state == STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)
    assert state.attributes.get(fan.ATTR_OSCILLATING) is True
    assert state.attributes.get(fan.ATTR_DIRECTION) == "reverse"

    await common.async_oscillate(hass, "fan.test", False)
    state = hass.states.get("fan.test")
    assert state.state == STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)
    assert state.attributes.get(fan.ATTR_OSCILLATING) is False

    await common.async_set_direction(hass, "fan.test", "forward")
    state = hass.states.get("fan.test")
    assert state.state == STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)
    assert state.attributes.get(fan.ATTR_OSCILLATING) is False
    assert state.attributes.get(fan.ATTR_DIRECTION) == "forward"