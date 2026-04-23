async def test_invalid_state_via_topic(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test handling of empty data via topic."""
    await mqtt_mock_entry()

    state = hass.states.get("light.test")
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get("rgb_color") is None
    assert state.attributes.get("rgbw_color") is None
    assert state.attributes.get("rgbww_color") is None
    assert state.attributes.get("brightness") is None
    assert state.attributes.get("color_temp_kelvin") is None
    assert state.attributes.get("effect") is None
    assert state.attributes.get("hs_color") is None
    assert state.attributes.get("xy_color") is None
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message(hass, "test_light_rgb/status", "1")
    async_fire_mqtt_message(hass, "test_light_rgb/color_mode/status", "rgb")
    async_fire_mqtt_message(hass, "test_light_rgb/rgb/status", "255,255,255")
    async_fire_mqtt_message(hass, "test_light_rgb/brightness/status", "255")
    async_fire_mqtt_message(hass, "test_light_rgb/effect/status", "none")

    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("rgb_color") == (255, 255, 255)
    assert state.attributes.get("brightness") == 255
    assert state.attributes.get("color_temp_kelvin") is None
    assert state.attributes.get("effect") == "none"
    assert state.attributes.get("hs_color") == (0, 0)
    assert state.attributes.get("xy_color") == (0.323, 0.329)
    assert state.attributes.get("color_mode") == "rgb"

    async_fire_mqtt_message(hass, "test_light_rgb/status", "")
    light_state = hass.states.get("light.test")
    assert state.state == STATE_ON

    async_fire_mqtt_message(hass, "test_light_rgb/brightness/status", "")
    light_state = hass.states.get("light.test")
    assert light_state.attributes["brightness"] == 255

    async_fire_mqtt_message(hass, "test_light_rgb/color_mode/status", "")
    light_state = hass.states.get("light.test")
    assert state.attributes.get("color_mode") == "rgb"

    async_fire_mqtt_message(hass, "test_light_rgb/effect/status", "")
    light_state = hass.states.get("light.test")
    assert light_state.attributes["effect"] == "none"

    async_fire_mqtt_message(hass, "test_light_rgb/rgb/status", "")
    light_state = hass.states.get("light.test")
    assert light_state.attributes.get("rgb_color") == (255, 255, 255)

    async_fire_mqtt_message(hass, "test_light_rgb/hs/status", "")
    light_state = hass.states.get("light.test")
    assert light_state.attributes.get("hs_color") == (0, 0)

    async_fire_mqtt_message(hass, "test_light_rgb/hs/status", "bad,bad")
    assert "Failed to parse hs state update" in caplog.text
    light_state = hass.states.get("light.test")
    assert light_state.attributes.get("hs_color") == (0, 0)

    async_fire_mqtt_message(hass, "test_light_rgb/xy/status", "")
    light_state = hass.states.get("light.test")
    assert light_state.attributes.get("xy_color") == (0.323, 0.329)

    async_fire_mqtt_message(hass, "test_light_rgb/rgbw/status", "255,255,255,1")
    async_fire_mqtt_message(hass, "test_light_rgb/color_mode/status", "rgbw")
    async_fire_mqtt_message(hass, "test_light_rgb/rgbw/status", "")
    light_state = hass.states.get("light.test")
    assert light_state.attributes.get("rgbw_color") == (255, 255, 255, 1)

    async_fire_mqtt_message(hass, "test_light_rgb/rgbww/status", "255,255,255,1,2")
    async_fire_mqtt_message(hass, "test_light_rgb/color_mode/status", "rgbww")
    async_fire_mqtt_message(hass, "test_light_rgb/rgbww/status", "")
    light_state = hass.states.get("light.test")
    assert light_state.attributes.get("rgbww_color") == (255, 255, 255, 1, 2)

    async_fire_mqtt_message(hass, "test_light_rgb/color_temp/status", "153")
    async_fire_mqtt_message(hass, "test_light_rgb/color_mode/status", "color_temp")

    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("rgb_color") == (255, 255, 251)
    assert state.attributes.get("brightness") == 255
    assert state.attributes.get("color_temp_kelvin") == 6535
    assert state.attributes.get("effect") == "none"
    assert state.attributes.get("hs_color") == (54.768, 1.6)
    assert state.attributes.get("xy_color") == (0.325, 0.333)

    async_fire_mqtt_message(hass, "test_light_rgb/color_temp/status", "")
    light_state = hass.states.get("light.test")
    assert light_state.attributes["color_temp_kelvin"] == 6535