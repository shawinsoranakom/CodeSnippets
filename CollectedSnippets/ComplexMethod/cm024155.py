async def test_invalid_values(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that invalid color/brightness/etc. values are ignored."""
    await mqtt_mock_entry()

    state = hass.states.get("light.test")
    assert state.state == STATE_UNKNOWN
    color_modes = [light.ColorMode.COLOR_TEMP, light.ColorMode.HS]
    assert state.attributes.get(light.ATTR_SUPPORTED_COLOR_MODES) == color_modes
    expected_features = (
        light.LightEntityFeature.FLASH | light.LightEntityFeature.TRANSITION
    )
    assert state.attributes.get(ATTR_SUPPORTED_FEATURES) is expected_features
    assert state.attributes.get("rgb_color") is None
    assert state.attributes.get("brightness") is None
    assert state.attributes.get("color_temp_kelvin") is None
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    # Turn on the light
    async_fire_mqtt_message(
        hass,
        "test_light_rgb",
        '{"state":"ON",'
        '"color":{"r":255,"g":255,"b":255},'
        '"brightness": 255,'
        '"color_mode": "color_temp",'
        '"color_temp": 100,'
        '"effect": "rainbow"}',
    )

    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    # Color converttrd from color_temp to rgb
    assert state.attributes.get("rgb_color") == (202, 218, 255)
    assert state.attributes.get("brightness") == 255
    assert state.attributes.get("color_temp_kelvin") == 10000
    # Empty color value
    async_fire_mqtt_message(
        hass,
        "test_light_rgb",
        '{"state":"ON", "color":{}, "color_mode": "rgb"}',
    )

    # Color should not have changed
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("rgb_color") == (202, 218, 255)

    # Bad HS color values
    async_fire_mqtt_message(
        hass,
        "test_light_rgb",
        '{"state":"ON", "color":{"h":"bad","s":"val"}, "color_mode": "hs"}',
    )

    # Color should not have changed
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("rgb_color") == (202, 218, 255)

    # Bad RGB color values
    async_fire_mqtt_message(
        hass,
        "test_light_rgb",
        '{"state":"ON", "color":{"r":"bad","g":"val","b":"test"}, "color_mode": "rgb"}',
    )

    # Color should not have changed
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("rgb_color") == (202, 218, 255)

    # Bad XY color values
    async_fire_mqtt_message(
        hass,
        "test_light_rgb",
        '{"state":"ON", "color":{"x":"bad","y":"val"}, "color_mode": "xy"}',
    )

    # Color should not have changed
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("rgb_color") == (202, 218, 255)

    # Bad brightness values
    async_fire_mqtt_message(
        hass, "test_light_rgb", '{"state":"ON", "brightness": "badValue"}'
    )

    # Brightness should not have changed
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("brightness") == 255

    # Unset color and set a valid color temperature
    async_fire_mqtt_message(
        hass,
        "test_light_rgb",
        '{"state":"ON", "color": null, "color_temp": 100, "color_mode": "color_temp"}',
    )
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("color_temp_kelvin") == 10000

    # Bad color temperature
    async_fire_mqtt_message(
        hass,
        "test_light_rgb",
        '{"state":"ON", "color_temp": "badValue", "color_mode": "color_temp"}',
    )
    assert (
        "Invalid or incomplete color value '{'state': 'ON', 'color_temp': "
        "'badValue', 'color_mode': 'color_temp'}' "
        "received for entity light.test" in caplog.text
    )

    # Color temperature should not have changed
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("color_temp_kelvin") == 10000