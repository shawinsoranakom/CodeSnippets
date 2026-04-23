async def test_brightness_only(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test brightness only light.

    There are two possible configurations for brightness only light:
    1) Set up "brightness" as supported color mode.
    2) Set "brightness" flag to true.
    """
    await mqtt_mock_entry()

    state = hass.states.get("light.test")
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get(light.ATTR_SUPPORTED_COLOR_MODES) == [
        light.ColorMode.BRIGHTNESS
    ]
    expected_features = (
        light.LightEntityFeature.FLASH | light.LightEntityFeature.TRANSITION
    )
    assert state.attributes.get(ATTR_SUPPORTED_FEATURES) == expected_features
    assert state.attributes.get("rgb_color") is None
    assert state.attributes.get("brightness") is None
    assert state.attributes.get("color_temp_kelvin") is None
    assert state.attributes.get("effect") is None
    assert state.attributes.get("xy_color") is None
    assert state.attributes.get("hs_color") is None

    async_fire_mqtt_message(hass, "test_light_rgb", '{"state":"ON", "brightness": 50}')

    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("rgb_color") is None
    assert state.attributes.get("brightness") == 50
    assert state.attributes.get("color_temp_kelvin") is None
    assert state.attributes.get("effect") is None
    assert state.attributes.get("xy_color") is None
    assert state.attributes.get("hs_color") is None

    async_fire_mqtt_message(hass, "test_light_rgb", '{"state":"OFF"}')

    state = hass.states.get("light.test")
    assert state.state == STATE_OFF