async def test_controlling_state_and_attributes_with_json_message_without_template(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test the controlling state via topic and JSON message without a value template."""
    await mqtt_mock_entry()

    state = hass.states.get("siren.test")
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get(siren.ATTR_TONE) is None
    assert state.attributes.get(siren.ATTR_DURATION) is None
    assert state.attributes.get(siren.ATTR_VOLUME_LEVEL) is None

    async_fire_mqtt_message(
        hass,
        "state-topic",
        '{"state":"beer on", "tone": "bell", "duration": 10, "volume_level": 0.5 }',
    )

    state = hass.states.get("siren.test")
    assert state.state == STATE_ON
    assert state.attributes.get(siren.ATTR_TONE) == "bell"
    assert state.attributes.get(siren.ATTR_DURATION) == 10
    assert state.attributes.get(siren.ATTR_VOLUME_LEVEL) == 0.5

    async_fire_mqtt_message(
        hass,
        "state-topic",
        '{"state":"beer off", "tone": "bell", "duration": 5, "volume_level": 0.6}',
    )

    state = hass.states.get("siren.test")
    assert state.state == STATE_OFF
    assert state.attributes.get(siren.ATTR_TONE) == "bell"
    assert state.attributes.get(siren.ATTR_DURATION) == 5
    assert state.attributes.get(siren.ATTR_VOLUME_LEVEL) == 0.6

    # Test validation of received attributes, invalid
    async_fire_mqtt_message(
        hass,
        "state-topic",
        '{"state":"beer on", "duration": 6, "volume_level": 2,"tone": "ping"}',
    )
    state = hass.states.get("siren.test")
    assert (
        "Unable to update siren state attributes from payload '{'duration': 6, 'volume_level': 2, 'tone': 'ping'}': value must be at most 1 for dictionary value @ data['volume_level']"
        in caplog.text
    )
    # Only the on/of state was updated, not the attributes
    assert state.state == STATE_ON
    assert state.attributes.get(siren.ATTR_TONE) == "bell"
    assert state.attributes.get(siren.ATTR_DURATION) == 5
    assert state.attributes.get(siren.ATTR_VOLUME_LEVEL) == 0.6

    async_fire_mqtt_message(
        hass,
        "state-topic",
        "{}",
    )
    assert state.state == STATE_ON
    assert state.attributes.get(siren.ATTR_TONE) == "bell"
    assert state.attributes.get(siren.ATTR_DURATION) == 5
    assert state.attributes.get(siren.ATTR_VOLUME_LEVEL) == 0.6