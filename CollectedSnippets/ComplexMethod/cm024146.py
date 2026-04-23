async def test_color_temp_only(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test a light that only support color_temp as supported color mode."""
    await mqtt_mock_entry()

    state = hass.states.get("light.test")
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get(light.ATTR_SUPPORTED_COLOR_MODES) == [
        light.ColorMode.COLOR_TEMP
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

    async_fire_mqtt_message(
        hass,
        "test_light_rgb",
        '{"state":"ON", "color_mode": "color_temp", "color_temp": 250, "brightness": 50}',
    )

    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("rgb_color") == (255, 206, 166)
    assert state.attributes.get("brightness") == 50
    assert state.attributes.get("color_temp_kelvin") == 4000
    assert state.attributes.get("effect") is None
    assert state.attributes.get("xy_color") == (0.42, 0.365)
    assert state.attributes.get("hs_color") == (26.812, 34.87)

    async_fire_mqtt_message(hass, "test_light_rgb", '{"state":"OFF"}')

    state = hass.states.get("light.test")
    assert state.state == STATE_OFF