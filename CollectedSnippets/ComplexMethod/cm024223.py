async def test_brightness_controlling_scale(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test the brightness controlling scale."""
    await mqtt_mock_entry()

    state = hass.states.get("light.test")
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get("brightness") is None
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message(hass, "test_scale/status", "on")

    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("brightness") is None

    async_fire_mqtt_message(hass, "test_scale/status", "off")

    state = hass.states.get("light.test")
    assert state.state == STATE_OFF

    async_fire_mqtt_message(hass, "test_scale/status", "on")

    async_fire_mqtt_message(hass, "test_scale/brightness/status", "99")

    light_state = hass.states.get("light.test")
    assert light_state.attributes["brightness"] == 255