async def test_turn_on_with_unknown_color_mode_optimistic(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test setup and turn with unknown color_mode in optimistic mode."""
    await mqtt_mock_entry()
    state = hass.states.get("light.test")
    assert state.state == STATE_UNKNOWN

    # Turn on the light without brightness or color_temp attributes
    await common.async_turn_on(hass, "light.test")
    state = hass.states.get("light.test")
    assert state.attributes.get("color_mode") == light.ColorMode.UNKNOWN
    assert state.attributes.get("brightness") is None
    assert state.attributes.get("color_temp_kelvin") is None
    assert state.state == STATE_ON

    # Turn on the light with brightness or color_temp attributes
    await common.async_turn_on(
        hass, "light.test", brightness=50, color_temp_kelvin=5208
    )
    state = hass.states.get("light.test")
    assert state.attributes.get("color_mode") == light.ColorMode.COLOR_TEMP
    assert state.attributes.get("brightness") == 50
    assert state.attributes.get("color_temp_kelvin") == 5208
    assert state.state == STATE_ON