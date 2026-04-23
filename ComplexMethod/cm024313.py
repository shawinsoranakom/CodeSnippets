async def test_sending_mqtt_commands_and_explicit_optimistic(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test optimistic mode with state topic and turn on attributes."""
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

    with pytest.raises(NotValidPresetModeError) as exc:
        await common.async_turn_on(hass, "fan.test", preset_mode="auto")
    assert exc.value.translation_key == "not_valid_preset_mode"
    assert mqtt_mock.async_publish.call_count == 0
    mqtt_mock.async_publish.reset_mock()

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

    await common.async_turn_off(hass, "fan.test")
    mqtt_mock.async_publish.assert_any_call("command-topic", "OFF", 0, False)
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test")
    assert state.state == STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_turn_on(hass, "fan.test", preset_mode="silent")
    assert mqtt_mock.async_publish.call_count == 2
    mqtt_mock.async_publish.assert_any_call("command-topic", "ON", 0, False)
    mqtt_mock.async_publish.assert_any_call(
        "preset-mode-command-topic", "silent", 0, False
    )
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

    await common.async_turn_on(hass, "fan.test", preset_mode="silent")
    assert mqtt_mock.async_publish.call_count == 2
    mqtt_mock.async_publish.assert_any_call("command-topic", "ON", 0, False)
    mqtt_mock.async_publish.assert_any_call(
        "preset-mode-command-topic", "silent", 0, False
    )
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

    await common.async_set_direction(hass, "fan.test", "forward")
    mqtt_mock.async_publish.assert_called_once_with(
        "direction-command-topic", "forward", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test")
    assert state.state == STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_oscillate(hass, "fan.test", True)
    mqtt_mock.async_publish.assert_called_once_with(
        "oscillation-command-topic", "oscillate_on", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test")
    assert state.state == STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_turn_on(hass, "fan.test", percentage=50)
    assert mqtt_mock.async_publish.call_count == 2
    mqtt_mock.async_publish.assert_any_call("command-topic", "ON", 0, False)
    mqtt_mock.async_publish.assert_any_call("percentage-command-topic", "50", 0, False)
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

    await common.async_set_direction(hass, "fan.test", "reverse")
    mqtt_mock.async_publish.assert_called_once_with(
        "direction-command-topic", "reverse", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test")
    assert state.state == STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_oscillate(hass, "fan.test", False)
    mqtt_mock.async_publish.assert_called_once_with(
        "oscillation-command-topic", "oscillate_off", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test")
    assert state.state == STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_set_percentage(hass, "fan.test", 33)
    mqtt_mock.async_publish.assert_called_once_with(
        "percentage-command-topic", "33", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test")
    assert state.state == STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_set_percentage(hass, "fan.test", 50)
    mqtt_mock.async_publish.assert_called_once_with(
        "percentage-command-topic", "50", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test")
    assert state.state == STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_set_percentage(hass, "fan.test", 100)
    mqtt_mock.async_publish.assert_called_once_with(
        "percentage-command-topic", "100", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test")
    assert state.state == STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_set_percentage(hass, "fan.test", 0)
    mqtt_mock.async_publish.assert_called_once_with(
        "percentage-command-topic", "0", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test")
    assert state.state == STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    with pytest.raises(MultipleInvalid):
        await common.async_set_percentage(hass, "fan.test", 101)

    with pytest.raises(NotValidPresetModeError) as exc:
        await common.async_set_preset_mode(hass, "fan.test", "low")
    assert exc.value.translation_key == "not_valid_preset_mode"

    with pytest.raises(NotValidPresetModeError) as exc:
        await common.async_set_preset_mode(hass, "fan.test", "medium")
    assert exc.value.translation_key == "not_valid_preset_mode"

    await common.async_set_preset_mode(hass, "fan.test", "whoosh")
    mqtt_mock.async_publish.assert_called_once_with(
        "preset-mode-command-topic", "whoosh", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test")
    assert state.state == STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_set_preset_mode(hass, "fan.test", "silent")
    mqtt_mock.async_publish.assert_called_once_with(
        "preset-mode-command-topic", "silent", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test")
    assert state.state == STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    with pytest.raises(NotValidPresetModeError) as exc:
        await common.async_set_preset_mode(hass, "fan.test", "freaking-high")
    assert exc.value.translation_key == "not_valid_preset_mode"

    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test")
    assert state.state == STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)