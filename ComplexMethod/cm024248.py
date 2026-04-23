async def test_controlling_state_via_topic(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test the controlling state via topic."""
    await mqtt_mock_entry()

    state = hass.states.get("humidifier.test")
    assert state.state == STATE_UNKNOWN
    assert not state.attributes.get(ATTR_ASSUMED_STATE)
    assert not state.attributes.get(humidifier.ATTR_ACTION)

    async_fire_mqtt_message(hass, "state-topic", "StAtE_On")
    state = hass.states.get("humidifier.test")
    assert state.state == STATE_ON
    assert not state.attributes.get(humidifier.ATTR_ACTION)

    async_fire_mqtt_message(hass, "state-topic", "StAtE_OfF")
    state = hass.states.get("humidifier.test")
    assert state.state == STATE_OFF
    assert not state.attributes.get(humidifier.ATTR_ACTION)

    async_fire_mqtt_message(hass, "humidity-state-topic", "0")
    state = hass.states.get("humidifier.test")
    assert state.attributes.get(humidifier.ATTR_HUMIDITY) == 0

    async_fire_mqtt_message(hass, "humidity-state-topic", "25")
    state = hass.states.get("humidifier.test")
    assert state.attributes.get(humidifier.ATTR_HUMIDITY) == 25

    async_fire_mqtt_message(hass, "humidity-state-topic", "50")
    state = hass.states.get("humidifier.test")
    assert state.attributes.get(humidifier.ATTR_HUMIDITY) == 50

    async_fire_mqtt_message(hass, "humidity-state-topic", "100")
    state = hass.states.get("humidifier.test")
    assert state.attributes.get(humidifier.ATTR_HUMIDITY) == 100

    async_fire_mqtt_message(hass, "humidity-state-topic", "101")
    assert "not a valid target humidity" in caplog.text
    caplog.clear()

    async_fire_mqtt_message(hass, "humidity-state-topic", "invalid")
    assert "not a valid target humidity" in caplog.text
    caplog.clear()

    async_fire_mqtt_message(hass, "mode-state-topic", "low")
    assert "not a valid mode" in caplog.text
    caplog.clear()

    async_fire_mqtt_message(hass, "current-humidity-topic", "48")
    state = hass.states.get("humidifier.test")
    assert state.attributes.get(humidifier.ATTR_CURRENT_HUMIDITY) == 48

    async_fire_mqtt_message(hass, "current-humidity-topic", "101")
    state = hass.states.get("humidifier.test")
    assert state.attributes.get(humidifier.ATTR_CURRENT_HUMIDITY) == 48

    async_fire_mqtt_message(hass, "current-humidity-topic", "-1.6")
    state = hass.states.get("humidifier.test")
    assert state.attributes.get(humidifier.ATTR_CURRENT_HUMIDITY) == 48

    async_fire_mqtt_message(hass, "current-humidity-topic", "43.6")
    state = hass.states.get("humidifier.test")
    assert state.attributes.get(humidifier.ATTR_CURRENT_HUMIDITY) == 44

    async_fire_mqtt_message(hass, "current-humidity-topic", "invalid")
    state = hass.states.get("humidifier.test")
    assert state.attributes.get(humidifier.ATTR_CURRENT_HUMIDITY) == 44

    async_fire_mqtt_message(hass, "mode-state-topic", "auto")
    state = hass.states.get("humidifier.test")
    assert state.attributes.get(humidifier.ATTR_MODE) == "auto"

    async_fire_mqtt_message(hass, "mode-state-topic", "eco")
    state = hass.states.get("humidifier.test")
    assert state.attributes.get(humidifier.ATTR_MODE) == "eco"

    async_fire_mqtt_message(hass, "mode-state-topic", "baby")
    state = hass.states.get("humidifier.test")
    assert state.attributes.get(humidifier.ATTR_MODE) == "baby"

    async_fire_mqtt_message(hass, "mode-state-topic", "ModeUnknown")
    assert "not a valid mode" in caplog.text
    caplog.clear()

    async_fire_mqtt_message(hass, "mode-state-topic", "rEset_mode")
    state = hass.states.get("humidifier.test")
    assert state.attributes.get(humidifier.ATTR_MODE) is None

    async_fire_mqtt_message(hass, "humidity-state-topic", "rEset_humidity")
    state = hass.states.get("humidifier.test")
    assert state.attributes.get(humidifier.ATTR_HUMIDITY) is None

    async_fire_mqtt_message(hass, "state-topic", "None")
    state = hass.states.get("humidifier.test")
    assert state.state == STATE_UNKNOWN
    assert not state.attributes.get(humidifier.ATTR_ACTION)

    # Turn un the humidifier
    async_fire_mqtt_message(hass, "state-topic", "StAtE_On")
    state = hass.states.get("humidifier.test")
    assert state.state == STATE_ON
    assert not state.attributes.get(humidifier.ATTR_ACTION)

    async_fire_mqtt_message(hass, "action-topic", HumidifierAction.DRYING.value)
    state = hass.states.get("humidifier.test")
    assert state.attributes.get(humidifier.ATTR_ACTION) == HumidifierAction.DRYING

    async_fire_mqtt_message(hass, "action-topic", HumidifierAction.HUMIDIFYING.value)
    state = hass.states.get("humidifier.test")
    assert state.attributes.get(humidifier.ATTR_ACTION) == HumidifierAction.HUMIDIFYING

    async_fire_mqtt_message(hass, "action-topic", HumidifierAction.HUMIDIFYING.value)
    state = hass.states.get("humidifier.test")
    assert state.attributes.get(humidifier.ATTR_ACTION) == HumidifierAction.HUMIDIFYING

    async_fire_mqtt_message(hass, "action-topic", "invalid_action")
    state = hass.states.get("humidifier.test")
    assert state.attributes.get(humidifier.ATTR_ACTION) == HumidifierAction.HUMIDIFYING

    async_fire_mqtt_message(hass, "state-topic", "StAtE_OfF")
    state = hass.states.get("humidifier.test")
    assert state.state == STATE_OFF
    assert state.attributes.get(humidifier.ATTR_ACTION) == HumidifierAction.OFF