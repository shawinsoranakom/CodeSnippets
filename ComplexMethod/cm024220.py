async def test_controlling_color_mode_state_via_topic(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    payload: str,
    kelvin: int,
) -> None:
    """Test the controlling of the color mode state via topic."""
    color_modes = ["color_temp"]

    await mqtt_mock_entry()

    state = hass.states.get("light.test")
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get("color_temp_kelvin") is None
    assert state.attributes.get(light.ATTR_COLOR_MODE) is None
    assert state.attributes.get(light.ATTR_SUPPORTED_COLOR_MODES) == color_modes
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message(hass, "test_light_color_temp/status", "ON")
    async_fire_mqtt_message(hass, "test_light_color_temp/brightness/status", "70")
    async_fire_mqtt_message(hass, "test_light_color_temp/color_temp/status", payload)
    light_state = hass.states.get("light.test")
    assert light_state.attributes.get("brightness") == 70
    assert light_state.attributes["color_temp_kelvin"] == kelvin
    assert light_state.attributes.get(light.ATTR_COLOR_MODE) == "color_temp"
    assert light_state.attributes.get(light.ATTR_SUPPORTED_COLOR_MODES) == color_modes