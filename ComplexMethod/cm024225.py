async def test_controlling_state_via_topic_with_templates(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test the setting of the state with a template."""
    color_modes = ["color_temp", "hs", "rgb", "rgbw", "rgbww", "xy"]

    await mqtt_mock_entry()

    state = hass.states.get("light.test")
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get("brightness") is None
    assert state.attributes.get("rgb_color") is None

    async_fire_mqtt_message(hass, "test_light_rgb/rgb/status", '{"hello": [1, 2, 3]}')
    async_fire_mqtt_message(hass, "test_light_rgb/status", '{"hello": "ON"}')
    async_fire_mqtt_message(hass, "test_light_rgb/brightness/status", '{"hello": "50"}')
    async_fire_mqtt_message(
        hass, "test_light_rgb/effect/status", '{"hello": "rainbow"}'
    )
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("brightness") == 50
    assert state.attributes.get("rgb_color") == (1, 2, 3)
    assert state.attributes.get("effect") == "rainbow"
    assert state.attributes.get(light.ATTR_COLOR_MODE) == "rgb"
    assert state.attributes.get(light.ATTR_SUPPORTED_COLOR_MODES) == color_modes

    async_fire_mqtt_message(
        hass, "test_light_rgb/rgbw/status", '{"hello": [1, 2, 3, 4]}'
    )
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("rgbw_color") == (1, 2, 3, 4)
    assert state.attributes.get(light.ATTR_COLOR_MODE) == "rgbw"
    assert state.attributes.get(light.ATTR_SUPPORTED_COLOR_MODES) == color_modes

    async_fire_mqtt_message(
        hass, "test_light_rgb/rgbww/status", '{"hello": [1, 2, 3, 4, 5]}'
    )
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("rgbww_color") == (1, 2, 3, 4, 5)
    assert state.attributes.get(light.ATTR_COLOR_MODE) == "rgbww"
    assert state.attributes.get(light.ATTR_SUPPORTED_COLOR_MODES) == color_modes

    async_fire_mqtt_message(
        hass, "test_light_rgb/color_temp/status", '{"hello": "300"}'
    )
    state = hass.states.get("light.test")
    assert state.attributes.get("color_temp_kelvin") == 3333
    assert state.attributes.get(light.ATTR_COLOR_MODE) == "color_temp"
    assert state.attributes.get(light.ATTR_SUPPORTED_COLOR_MODES) == color_modes

    async_fire_mqtt_message(hass, "test_light_rgb/hs/status", '{"hello": [100,50]}')
    state = hass.states.get("light.test")
    assert state.attributes.get("hs_color") == (100, 50)
    assert state.attributes.get(light.ATTR_COLOR_MODE) == "hs"
    assert state.attributes.get(light.ATTR_SUPPORTED_COLOR_MODES) == color_modes

    async_fire_mqtt_message(
        hass, "test_light_rgb/xy/status", '{"hello": [0.123,0.123]}'
    )
    state = hass.states.get("light.test")
    assert state.attributes.get("xy_color") == (0.123, 0.123)
    assert state.attributes.get(light.ATTR_COLOR_MODE) == "xy"
    assert state.attributes.get(light.ATTR_SUPPORTED_COLOR_MODES) == color_modes

    async_fire_mqtt_message(hass, "test_light_rgb/brightness/status", '{"hello": 100}')
    state = hass.states.get("light.test")
    assert state.attributes.get("brightness") == 100

    async_fire_mqtt_message(hass, "test_light_rgb/brightness/status", '{"hello": 50}')
    state = hass.states.get("light.test")
    assert state.attributes.get("brightness") == 50

    # test zero brightness received is ignored
    async_fire_mqtt_message(hass, "test_light_rgb/brightness/status", '{"hello": 0}')
    state = hass.states.get("light.test")
    assert state.attributes.get("brightness") == 50