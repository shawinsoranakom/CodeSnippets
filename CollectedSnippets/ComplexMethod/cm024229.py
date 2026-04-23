async def test_white_state_update(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test state updates for RGB + white light."""
    color_modes = ["rgb", "white"]

    await mqtt_mock_entry()

    state = hass.states.get("light.test")
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get("brightness") is None
    assert state.attributes.get("rgb_color") is None
    assert state.attributes.get(light.ATTR_COLOR_MODE) is None
    assert state.attributes.get(light.ATTR_SUPPORTED_COLOR_MODES) == color_modes
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message(
        hass,
        "tasmota_B94927/tele/STATE",
        '{"POWER":"ON","Dimmer":50,"Color":"0,0,0,128","White":50}',
    )
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("brightness") == 128
    assert state.attributes.get("rgb_color") is None
    assert state.attributes.get(light.ATTR_COLOR_MODE) == "white"
    assert state.attributes.get(light.ATTR_SUPPORTED_COLOR_MODES) == color_modes

    async_fire_mqtt_message(
        hass,
        "tasmota_B94927/tele/STATE",
        '{"POWER":"ON","Dimmer":50,"Color":"128,64,32,0","White":0}',
    )
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("brightness") == 128
    assert state.attributes.get("rgb_color") == (128, 64, 32)
    assert state.attributes.get(light.ATTR_COLOR_MODE) == "rgb"
    assert state.attributes.get(light.ATTR_SUPPORTED_COLOR_MODES) == color_modes