async def test_no_color_brightness_color_temp_if_no_topics(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test for no RGB, brightness, color temp, effector XY."""
    await mqtt_mock_entry()

    state = hass.states.get("light.test")
    assert state.state == STATE_UNKNOWN
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

    async_fire_mqtt_message(hass, "test_light_rgb", '{"state":"ON"}')

    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("rgb_color") is None
    assert state.attributes.get("brightness") is None
    assert state.attributes.get("color_temp_kelvin") is None
    assert state.attributes.get("effect") is None
    assert state.attributes.get("xy_color") is None
    assert state.attributes.get("hs_color") is None

    async_fire_mqtt_message(hass, "test_light_rgb", '{"state":"OFF"}')

    state = hass.states.get("light.test")
    assert state.state == STATE_OFF

    async_fire_mqtt_message(hass, "test_light_rgb", '{"state": null}')

    state = hass.states.get("light.test")
    assert state.state == STATE_UNKNOWN