async def test_sending_mqtt_commands_and_optimistic(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test optimistic mode without state topic."""
    mqtt_mock = await mqtt_mock_entry()

    state = hass.states.get("humidifier.test")
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await async_turn_on(hass, "humidifier.test")
    mqtt_mock.async_publish.assert_called_once_with(
        "command-topic", "StAtE_On", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("humidifier.test")
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await async_turn_off(hass, "humidifier.test")
    mqtt_mock.async_publish.assert_called_once_with(
        "command-topic", "StAtE_OfF", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("humidifier.test")
    assert state.state == STATE_OFF
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    with pytest.raises(MultipleInvalid):
        await async_set_humidity(hass, "humidifier.test", -1)

    with pytest.raises(MultipleInvalid):
        await async_set_humidity(hass, "humidifier.test", 101)

    await async_set_humidity(hass, "humidifier.test", 100)
    mqtt_mock.async_publish.assert_called_once_with(
        "humidity-command-topic", "100", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("humidifier.test")
    assert state.attributes.get(humidifier.ATTR_HUMIDITY) == 100
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await async_set_humidity(hass, "humidifier.test", 0)
    mqtt_mock.async_publish.assert_called_once_with(
        "humidity-command-topic", "0", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("humidifier.test")
    assert state.attributes.get(humidifier.ATTR_HUMIDITY) == 0
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await async_set_mode(hass, "humidifier.test", "low")
    assert "not a valid mode" in caplog.text
    caplog.clear()

    await async_set_mode(hass, "humidifier.test", "auto")
    mqtt_mock.async_publish.assert_called_once_with(
        "mode-command-topic", "auto", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("humidifier.test")
    assert state.attributes.get(humidifier.ATTR_MODE) == "auto"
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await async_set_mode(hass, "humidifier.test", "eco")
    mqtt_mock.async_publish.assert_called_once_with(
        "mode-command-topic", "eco", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("humidifier.test")
    assert state.attributes.get(humidifier.ATTR_MODE) == "eco"
    assert state.attributes.get(ATTR_ASSUMED_STATE)