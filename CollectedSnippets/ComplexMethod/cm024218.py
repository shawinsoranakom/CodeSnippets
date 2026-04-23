async def test_no_color_brightness_color_temp_hs_white_xy_if_no_topics(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test if there is no color and brightness if no topic."""
    await mqtt_mock_entry()

    state = hass.states.get("light.test")
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get("rgb_color") is None
    assert state.attributes.get("brightness") is None
    assert state.attributes.get("color_temp_kelvin") is None
    assert state.attributes.get("hs_color") is None
    assert state.attributes.get("rgb_color") is None
    assert state.attributes.get("rgbw_color") is None
    assert state.attributes.get("rgbww_color") is None
    assert state.attributes.get("xy_color") is None
    assert state.attributes.get(light.ATTR_COLOR_MODE) is None
    assert state.attributes.get(light.ATTR_SUPPORTED_COLOR_MODES) == ["onoff"]

    async_fire_mqtt_message(hass, "test_light_rgb/status", "ON")

    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("rgb_color") is None
    assert state.attributes.get("brightness") is None
    assert state.attributes.get("color_temp_kelvin") is None
    assert state.attributes.get("hs_color") is None
    assert state.attributes.get("rgb_color") is None
    assert state.attributes.get("rgbw_color") is None
    assert state.attributes.get("rgbww_color") is None
    assert state.attributes.get("xy_color") is None
    assert state.attributes.get(light.ATTR_COLOR_MODE) == "onoff"
    assert state.attributes.get(light.ATTR_SUPPORTED_COLOR_MODES) == ["onoff"]

    async_fire_mqtt_message(hass, "test_light_rgb/status", "OFF")

    state = hass.states.get("light.test")
    assert state.state == STATE_OFF

    async_fire_mqtt_message(hass, "test_light_rgb/status", "None")

    state = hass.states.get("light.test")
    assert state.state == STATE_UNKNOWN