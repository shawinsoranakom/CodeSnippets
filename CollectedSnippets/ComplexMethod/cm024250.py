async def test_controlling_state_via_topic_and_json_message_shared_topic(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test the controlling state via topic and JSON message using a shared topic."""
    await mqtt_mock_entry()

    state = hass.states.get("humidifier.test")
    assert state.state == STATE_UNKNOWN
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message(
        hass,
        "shared-state-topic",
        '{"state":"ON","mode":"eco","humidity": 50}',
    )
    state = hass.states.get("humidifier.test")
    assert state.state == STATE_ON
    assert state.attributes.get(humidifier.ATTR_HUMIDITY) == 50
    assert state.attributes.get(humidifier.ATTR_MODE) == "eco"

    async_fire_mqtt_message(
        hass,
        "shared-state-topic",
        '{"state":"ON","mode":"auto","humidity": 10}',
    )
    state = hass.states.get("humidifier.test")
    assert state.state == STATE_ON
    assert state.attributes.get(humidifier.ATTR_HUMIDITY) == 10
    assert state.attributes.get(humidifier.ATTR_MODE) == "auto"

    async_fire_mqtt_message(
        hass,
        "shared-state-topic",
        '{"state":"OFF","mode":"auto","humidity": 0}',
    )
    state = hass.states.get("humidifier.test")
    assert state.state == STATE_OFF
    assert state.attributes.get(humidifier.ATTR_HUMIDITY) == 0
    assert state.attributes.get(humidifier.ATTR_MODE) == "auto"

    async_fire_mqtt_message(
        hass,
        "shared-state-topic",
        '{"humidity": 100}',
    )
    state = hass.states.get("humidifier.test")
    assert state.attributes.get(humidifier.ATTR_HUMIDITY) == 100
    assert state.attributes.get(humidifier.ATTR_MODE) == "auto"
    caplog.clear()