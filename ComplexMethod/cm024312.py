async def test_sending_mqtt_commands_and_optimistic_no_percentage_topic(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test optimistic mode without state topic without percentage command topic."""
    mqtt_mock = await mqtt_mock_entry()

    state = hass.states.get("fan.test")
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    with pytest.raises(NotValidPresetModeError) as exc:
        await common.async_set_preset_mode(hass, "fan.test", "medium")
    assert exc.value.translation_key == "not_valid_preset_mode"

    await common.async_set_preset_mode(hass, "fan.test", "whoosh")
    mqtt_mock.async_publish.assert_called_once_with(
        "preset-mode-command-topic", "whoosh", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test")
    assert state.attributes.get(fan.ATTR_PRESET_MODE) is None
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_set_preset_mode(hass, "fan.test", "breeze")
    mqtt_mock.async_publish.assert_called_once_with(
        "preset-mode-command-topic", "breeze", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test")
    assert state.attributes.get(fan.ATTR_PRESET_MODE) is None
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_set_preset_mode(hass, "fan.test", "silent")
    mqtt_mock.async_publish.assert_called_once_with(
        "preset-mode-command-topic", "silent", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test")
    assert state.attributes.get(fan.ATTR_PRESET_MODE) is None
    assert state.attributes.get(ATTR_ASSUMED_STATE)