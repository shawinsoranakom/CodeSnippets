async def test_effect(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test effect sent over MQTT in optimistic mode."""
    mqtt_mock = await mqtt_mock_entry()

    state = hass.states.get("light.test")
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get(ATTR_SUPPORTED_FEATURES) == 44

    await common.async_turn_on(hass, "light.test")
    mqtt_mock.async_publish.assert_called_once_with(
        "test_light_rgb/set", "on,", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert not state.attributes.get("effect")

    await common.async_turn_on(hass, "light.test", effect="rainbow")
    mqtt_mock.async_publish.assert_called_once_with(
        "test_light_rgb/set", "on,rainbow", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("effect") == "rainbow"

    await common.async_turn_on(hass, "light.test", effect="colorloop")
    mqtt_mock.async_publish.assert_called_once_with(
        "test_light_rgb/set", "on,colorloop", 0, False
    )
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("effect") == "colorloop"