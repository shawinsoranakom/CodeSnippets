async def test_attributes(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test attributes."""
    await mqtt_mock_entry()

    state = hass.states.get("humidifier.test")
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get(humidifier.ATTR_AVAILABLE_MODES) == [
        "eco",
        "baby",
    ]
    assert state.attributes.get(humidifier.ATTR_MIN_HUMIDITY) == 0
    assert state.attributes.get(humidifier.ATTR_MAX_HUMIDITY) == 100

    await async_turn_on(hass, "humidifier.test")
    state = hass.states.get("humidifier.test")
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_ASSUMED_STATE)
    assert state.attributes.get(humidifier.ATTR_HUMIDITY) is None
    assert state.attributes.get(humidifier.ATTR_MODE) is None

    await async_turn_off(hass, "humidifier.test")
    state = hass.states.get("humidifier.test")
    assert state.state == STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)
    assert state.attributes.get(humidifier.ATTR_HUMIDITY) is None
    assert state.attributes.get(humidifier.ATTR_MODE) is None