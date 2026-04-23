async def test_sending_mqtt_commands_with_alternate_speed_range(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test the controlling state via topic using an alternate speed range."""
    mqtt_mock = await mqtt_mock_entry()

    await common.async_set_percentage(hass, "fan.test1", 0)
    mqtt_mock.async_publish.assert_called_once_with(
        "percentage-command-topic1", "0", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test1")
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_set_percentage(hass, "fan.test1", 33)
    mqtt_mock.async_publish.assert_called_once_with(
        "percentage-command-topic1", "1", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test1")
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_set_percentage(hass, "fan.test1", 66)
    mqtt_mock.async_publish.assert_called_once_with(
        "percentage-command-topic1", "2", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test1")
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_set_percentage(hass, "fan.test1", 100)
    mqtt_mock.async_publish.assert_called_once_with(
        "percentage-command-topic1", "3", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test1")
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_set_percentage(hass, "fan.test2", 0)
    mqtt_mock.async_publish.assert_called_once_with(
        "percentage-command-topic2", "0", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test2")
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_set_percentage(hass, "fan.test2", 100)
    mqtt_mock.async_publish.assert_called_once_with(
        "percentage-command-topic2", "200", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test2")
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_set_percentage(hass, "fan.test3", 0)
    mqtt_mock.async_publish.assert_called_once_with(
        "percentage-command-topic3", "80", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test3")
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_set_percentage(hass, "fan.test3", 100)
    mqtt_mock.async_publish.assert_called_once_with(
        "percentage-command-topic3", "1023", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("fan.test3")
    assert state.attributes.get(ATTR_ASSUMED_STATE)