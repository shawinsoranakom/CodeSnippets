async def test_brightness_scale(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test for brightness scaling."""
    await mqtt_mock_entry()

    state = hass.states.get("light.test")
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get("brightness") is None
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    # Turn on the light
    async_fire_mqtt_message(hass, "test_light_bright_scale", '{"state":"ON"}')

    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("brightness") is None

    # Turn on the light with brightness
    async_fire_mqtt_message(
        hass, "test_light_bright_scale", '{"state":"ON", "brightness": 99}'
    )

    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("brightness") == 255

    # Turn on the light with half brightness
    async_fire_mqtt_message(
        hass, "test_light_bright_scale", '{"state":"ON", "brightness": 50}'
    )

    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("brightness") == 129

    # Test limmiting max brightness
    async_fire_mqtt_message(
        hass, "test_light_bright_scale", '{"state":"ON", "brightness": 103}'
    )

    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("brightness") == 255