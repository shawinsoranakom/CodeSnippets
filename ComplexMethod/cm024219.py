async def test_controlling_state_via_topic(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test the controlling of the state via topic."""
    color_modes = ["color_temp", "hs", "rgb", "rgbw", "rgbww", "xy"]

    await mqtt_mock_entry()

    state = hass.states.get("light.test")
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get("rgb_color") is None
    assert state.attributes.get("brightness") is None
    assert state.attributes.get("color_temp_kelvin") is None
    assert state.attributes.get("effect") is None
    assert state.attributes.get("hs_color") is None
    assert state.attributes.get("rgb_color") is None
    assert state.attributes.get("rgbw_color") is None
    assert state.attributes.get("rgbww_color") is None
    assert state.attributes.get("xy_color") is None
    assert state.attributes.get(light.ATTR_COLOR_MODE) is None
    assert state.attributes.get(light.ATTR_SUPPORTED_COLOR_MODES) == color_modes
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message(hass, "test_light_rgb/status", "1")
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("rgb_color") is None
    assert state.attributes.get("brightness") is None
    assert state.attributes.get("color_temp_kelvin") is None
    assert state.attributes.get("effect") is None
    assert state.attributes.get("hs_color") is None
    assert state.attributes.get("rgb_color") is None
    assert state.attributes.get("rgbw_color") is None
    assert state.attributes.get("rgbww_color") is None
    assert state.attributes.get("xy_color") is None
    assert state.attributes.get(light.ATTR_COLOR_MODE) == "unknown"
    assert state.attributes.get(light.ATTR_SUPPORTED_COLOR_MODES) == color_modes

    async_fire_mqtt_message(hass, "test_light_rgb/status", "0")
    state = hass.states.get("light.test")
    assert state.state == STATE_OFF

    async_fire_mqtt_message(hass, "test_light_rgb/status", "1")
    async_fire_mqtt_message(hass, "test_light_rgb/brightness/status", "100")
    light_state = hass.states.get("light.test")
    assert light_state.attributes.get("brightness") is None
    assert light_state.attributes.get(light.ATTR_COLOR_MODE) == "unknown"
    assert light_state.attributes.get(light.ATTR_SUPPORTED_COLOR_MODES) == color_modes

    async_fire_mqtt_message(hass, "test_light_rgb/color_temp/status", "300")
    light_state = hass.states.get("light.test")
    assert light_state.attributes.get("brightness") == 100
    assert light_state.attributes.get(light.ATTR_COLOR_TEMP_KELVIN) == 3333
    assert light_state.attributes.get(light.ATTR_COLOR_MODE) == "color_temp"
    assert light_state.attributes.get(light.ATTR_SUPPORTED_COLOR_MODES) == color_modes

    async_fire_mqtt_message(hass, "test_light_rgb/effect/status", "rainbow")
    light_state = hass.states.get("light.test")
    assert light_state.attributes["effect"] == "rainbow"
    assert light_state.attributes.get(light.ATTR_COLOR_MODE) == "color_temp"
    assert light_state.attributes.get(light.ATTR_SUPPORTED_COLOR_MODES) == color_modes

    async_fire_mqtt_message(hass, "test_light_rgb/rgb/status", "125,125,125")
    light_state = hass.states.get("light.test")
    assert light_state.attributes.get("rgb_color") == (125, 125, 125)
    assert light_state.attributes.get(light.ATTR_COLOR_MODE) == "rgb"
    assert light_state.attributes.get(light.ATTR_SUPPORTED_COLOR_MODES) == color_modes

    async_fire_mqtt_message(hass, "test_light_rgb/rgbw/status", "80,40,20,10")
    light_state = hass.states.get("light.test")
    assert light_state.attributes.get("rgbw_color") == (80, 40, 20, 10)
    assert light_state.attributes.get(light.ATTR_COLOR_MODE) == "rgbw"
    assert light_state.attributes.get(light.ATTR_SUPPORTED_COLOR_MODES) == color_modes

    async_fire_mqtt_message(hass, "test_light_rgb/rgbww/status", "80,40,20,10,8")
    light_state = hass.states.get("light.test")
    assert light_state.attributes.get("rgbww_color") == (80, 40, 20, 10, 8)
    assert light_state.attributes.get(light.ATTR_COLOR_MODE) == "rgbww"
    assert light_state.attributes.get(light.ATTR_SUPPORTED_COLOR_MODES) == color_modes

    async_fire_mqtt_message(hass, "test_light_rgb/hs/status", "200,50")
    light_state = hass.states.get("light.test")
    assert light_state.attributes.get("hs_color") == (200, 50)
    assert light_state.attributes.get(light.ATTR_COLOR_MODE) == "hs"
    assert light_state.attributes.get(light.ATTR_SUPPORTED_COLOR_MODES) == color_modes

    async_fire_mqtt_message(hass, "test_light_rgb/xy/status", "0.675,0.322")
    light_state = hass.states.get("light.test")
    assert light_state.attributes.get("xy_color") == (0.675, 0.322)
    assert light_state.attributes.get(light.ATTR_COLOR_MODE) == "xy"
    assert light_state.attributes.get(light.ATTR_SUPPORTED_COLOR_MODES) == color_modes