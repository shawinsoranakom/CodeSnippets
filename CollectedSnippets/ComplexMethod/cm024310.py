async def test_sending_mqtt_commands_and_optimistic_no_legacy(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test optimistic mode without state topic without legacy speed command topic."""
    mqtt_mock = await mqtt_mock_entry()

    state = hass.states.get("fan.test")
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_turn_on(hass, "fan.test")
    mqtt_mock.async_publish.assert_called_once_with("command-topic", "ON", 0, False)
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test")
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_turn_off(hass, "fan.test")
    mqtt_mock.async_publish.assert_called_once_with("command-topic", "OFF", 0, False)
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test")
    assert state.state == STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    with pytest.raises(MultipleInvalid):
        await common.async_set_percentage(hass, "fan.test", -1)

    with pytest.raises(MultipleInvalid):
        await common.async_set_percentage(hass, "fan.test", 101)

    await common.async_set_percentage(hass, "fan.test", 100)
    mqtt_mock.async_publish.assert_called_once_with(
        "percentage-command-topic", "100", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test")
    assert state.attributes.get(fan.ATTR_PERCENTAGE) == 100
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_set_percentage(hass, "fan.test", 0)
    mqtt_mock.async_publish.assert_called_once_with(
        "percentage-command-topic", "0", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test")
    assert state.attributes.get(fan.ATTR_PERCENTAGE) == 0
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    with pytest.raises(NotValidPresetModeError) as exc:
        await common.async_set_preset_mode(hass, "fan.test", "low")
    assert exc.value.translation_key == "not_valid_preset_mode"

    with pytest.raises(NotValidPresetModeError) as exc:
        await common.async_set_preset_mode(hass, "fan.test", "auto")
    assert exc.value.translation_key == "not_valid_preset_mode"

    await common.async_set_preset_mode(hass, "fan.test", "whoosh")
    mqtt_mock.async_publish.assert_called_once_with(
        "preset-mode-command-topic", "whoosh", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test")
    assert state.attributes.get(fan.ATTR_PRESET_MODE) == "whoosh"
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_set_preset_mode(hass, "fan.test", "breeze")
    mqtt_mock.async_publish.assert_called_once_with(
        "preset-mode-command-topic", "breeze", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test")
    assert state.attributes.get(fan.ATTR_PRESET_MODE) == "breeze"
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_set_preset_mode(hass, "fan.test", "silent")
    mqtt_mock.async_publish.assert_called_once_with(
        "preset-mode-command-topic", "silent", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test")
    assert state.attributes.get(fan.ATTR_PRESET_MODE) == "silent"
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_turn_on(hass, "fan.test", percentage=25)
    assert mqtt_mock.async_publish.call_count == 2
    mqtt_mock.async_publish.assert_any_call("command-topic", "ON", 0, False)
    mqtt_mock.async_publish.assert_any_call("percentage-command-topic", "25", 0, False)
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test")
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_turn_off(hass, "fan.test")
    mqtt_mock.async_publish.assert_any_call("command-topic", "OFF", 0, False)
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test")
    assert state.state == STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_turn_on(hass, "fan.test", preset_mode="whoosh")
    assert mqtt_mock.async_publish.call_count == 2
    mqtt_mock.async_publish.assert_any_call("command-topic", "ON", 0, False)
    mqtt_mock.async_publish.assert_any_call(
        "preset-mode-command-topic", "whoosh", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test")
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    with pytest.raises(NotValidPresetModeError) as exc:
        await common.async_turn_on(hass, "fan.test", preset_mode="freaking-high")
    assert exc.value.translation_key == "not_valid_preset_mode"