async def test_controlling_state_with_unknown_color_mode(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test setup and turn with unknown color_mode in optimistic mode."""
    await mqtt_mock_entry()
    state = hass.states.get("light.test")
    assert state.state == STATE_UNKNOWN

    # Send `on` state but omit other attributes
    async_fire_mqtt_message(
        hass,
        "test_light",
        '{"state": "ON"}',
    )
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get(light.ATTR_COLOR_TEMP_KELVIN) is None
    assert state.attributes.get(light.ATTR_BRIGHTNESS) is None
    assert state.attributes.get(light.ATTR_COLOR_MODE) == light.ColorMode.UNKNOWN

    # Send complete light state
    async_fire_mqtt_message(
        hass,
        "test_light",
        '{"state": "ON", "brightness": 50, "color_mode": "color_temp", "color_temp": 192}',
    )
    state = hass.states.get("light.test")
    assert state.state == STATE_ON

    assert state.attributes.get(light.ATTR_COLOR_TEMP_KELVIN) == 5208
    assert state.attributes.get(light.ATTR_BRIGHTNESS) == 50
    assert state.attributes.get(light.ATTR_COLOR_MODE) == light.ColorMode.COLOR_TEMP