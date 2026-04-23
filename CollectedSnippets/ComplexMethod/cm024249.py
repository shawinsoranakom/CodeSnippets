async def test_controlling_state_via_topic_and_json_message(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test the controlling state via topic and JSON message."""
    await hass.async_block_till_done()
    await mqtt_mock_entry()

    state = hass.states.get("humidifier.test")
    assert state.state == STATE_UNKNOWN
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message(hass, "state-topic", '{"val":"ON"}')
    state = hass.states.get("humidifier.test")
    assert state.state == STATE_ON

    async_fire_mqtt_message(hass, "state-topic", '{"val":"OFF"}')
    state = hass.states.get("humidifier.test")
    assert state.state == STATE_OFF

    async_fire_mqtt_message(hass, "humidity-state-topic", '{"val": 1}')
    state = hass.states.get("humidifier.test")
    assert state.attributes.get(humidifier.ATTR_HUMIDITY) == 1

    async_fire_mqtt_message(hass, "humidity-state-topic", '{"val": 100}')
    state = hass.states.get("humidifier.test")
    assert state.attributes.get(humidifier.ATTR_HUMIDITY) == 100

    async_fire_mqtt_message(hass, "humidity-state-topic", '{"val": "None"}')
    state = hass.states.get("humidifier.test")
    assert state.attributes.get(humidifier.ATTR_HUMIDITY) is None

    async_fire_mqtt_message(hass, "humidity-state-topic", '{"otherval": 100}')
    assert state.attributes.get(humidifier.ATTR_HUMIDITY) is None
    caplog.clear()

    async_fire_mqtt_message(hass, "current-humidity-topic", '{"val": 1}')
    state = hass.states.get("humidifier.test")
    assert state.attributes.get(humidifier.ATTR_CURRENT_HUMIDITY) == 1

    async_fire_mqtt_message(hass, "current-humidity-topic", '{"val": 100}')
    state = hass.states.get("humidifier.test")
    assert state.attributes.get(humidifier.ATTR_CURRENT_HUMIDITY) == 100

    async_fire_mqtt_message(hass, "current-humidity-topic", '{"val": "None"}')
    state = hass.states.get("humidifier.test")
    assert state.attributes.get(humidifier.ATTR_CURRENT_HUMIDITY) is None

    async_fire_mqtt_message(hass, "current-humidity-topic", '{"otherval": 100}')
    assert state.attributes.get(humidifier.ATTR_CURRENT_HUMIDITY) is None
    caplog.clear()

    async_fire_mqtt_message(hass, "mode-state-topic", '{"val": "low"}')
    assert "not a valid mode" in caplog.text
    caplog.clear()

    async_fire_mqtt_message(hass, "mode-state-topic", '{"val": "auto"}')
    state = hass.states.get("humidifier.test")
    assert state.attributes.get(humidifier.ATTR_MODE) == "auto"

    async_fire_mqtt_message(hass, "mode-state-topic", '{"val": "eco"}')
    state = hass.states.get("humidifier.test")
    assert state.attributes.get(humidifier.ATTR_MODE) == "eco"

    async_fire_mqtt_message(hass, "mode-state-topic", '{"val": "baby"}')
    state = hass.states.get("humidifier.test")
    assert state.attributes.get(humidifier.ATTR_MODE) == "baby"

    async_fire_mqtt_message(hass, "mode-state-topic", '{"val": "None"}')
    state = hass.states.get("humidifier.test")
    assert state.attributes.get(humidifier.ATTR_MODE) is None

    async_fire_mqtt_message(hass, "mode-state-topic", '{"otherval": 100}')
    assert state.attributes.get(humidifier.ATTR_MODE) is None
    caplog.clear()

    async_fire_mqtt_message(hass, "state-topic", '{"val": null}')
    state = hass.states.get("humidifier.test")
    assert state.state == STATE_UNKNOWN

    # Make sure the humidifier is ON
    async_fire_mqtt_message(hass, "state-topic", '{"val":"ON"}')
    state = hass.states.get("humidifier.test")
    assert state.state == STATE_ON

    async_fire_mqtt_message(hass, "action-topic", '{"val": "drying"}')
    state = hass.states.get("humidifier.test")
    assert state.attributes.get(humidifier.ATTR_ACTION) == HumidifierAction.DRYING

    async_fire_mqtt_message(hass, "action-topic", '{"val": "humidifying"}')
    state = hass.states.get("humidifier.test")
    assert state.attributes.get(humidifier.ATTR_ACTION) == HumidifierAction.HUMIDIFYING

    async_fire_mqtt_message(hass, "action-topic", '{"val": null}')
    state = hass.states.get("humidifier.test")
    assert state.attributes.get(humidifier.ATTR_ACTION) == HumidifierAction.HUMIDIFYING

    async_fire_mqtt_message(hass, "action-topic", '{"otherval": "idle"}')
    state = hass.states.get("humidifier.test")
    assert state.attributes.get(humidifier.ATTR_ACTION) == HumidifierAction.HUMIDIFYING

    async_fire_mqtt_message(hass, "action-topic", '{"val": "idle"}')
    state = hass.states.get("humidifier.test")
    assert state.attributes.get(humidifier.ATTR_ACTION) == HumidifierAction.IDLE

    async_fire_mqtt_message(hass, "action-topic", '{"val": "off"}')
    state = hass.states.get("humidifier.test")
    assert state.attributes.get(humidifier.ATTR_ACTION) == HumidifierAction.OFF