async def test_white_scale(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test for white scaling."""
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
        hass,
        "test_light_bright_scale",
        '{"state":"ON", "brightness": 99, "color_mode":"hs", "color":{"h":180,"s":50}}',
    )

    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("brightness") == 255

    # Turn on the light with white - white_scale is NOT used
    async_fire_mqtt_message(
        hass,
        "test_light_bright_scale",
        '{"state":"ON", "color_mode":"white", "brightness": 50}',
    )

    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("brightness") == 129