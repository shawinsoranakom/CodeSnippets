async def test_filtering_not_supported_attributes_via_state(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test setting attributes with support flags via state."""
    await mqtt_mock_entry()

    state1 = hass.states.get("siren.test1")
    assert state1.state == STATE_UNKNOWN
    assert siren.ATTR_DURATION not in state1.attributes
    assert siren.ATTR_AVAILABLE_TONES in state1.attributes
    assert siren.ATTR_TONE in state1.attributes
    assert siren.ATTR_VOLUME_LEVEL in state1.attributes
    async_fire_mqtt_message(
        hass,
        "state-topic1",
        '{"state":"ON", "duration": 22, "tone": "ping", "volume_level": 0.88}',
    )
    await hass.async_block_till_done()
    state1 = hass.states.get("siren.test1")
    assert state1.attributes.get(siren.ATTR_TONE) == "ping"
    assert state1.attributes.get(siren.ATTR_DURATION) is None
    assert state1.attributes.get(siren.ATTR_VOLUME_LEVEL) == 0.88

    state2 = hass.states.get("siren.test2")
    assert siren.ATTR_DURATION in state2.attributes
    assert siren.ATTR_AVAILABLE_TONES in state2.attributes
    assert siren.ATTR_TONE in state2.attributes
    assert siren.ATTR_VOLUME_LEVEL not in state2.attributes
    async_fire_mqtt_message(
        hass,
        "state-topic2",
        '{"state":"ON", "duration": 22, "tone": "ping", "volume_level": 0.88}',
    )
    await hass.async_block_till_done()
    state2 = hass.states.get("siren.test2")
    assert state2.attributes.get(siren.ATTR_TONE) == "ping"
    assert state2.attributes.get(siren.ATTR_DURATION) == 22
    assert state2.attributes.get(siren.ATTR_VOLUME_LEVEL) is None

    state3 = hass.states.get("siren.test3")
    assert siren.ATTR_DURATION in state3.attributes
    assert siren.ATTR_AVAILABLE_TONES not in state3.attributes
    assert siren.ATTR_TONE not in state3.attributes
    assert siren.ATTR_VOLUME_LEVEL in state3.attributes
    async_fire_mqtt_message(
        hass,
        "state-topic3",
        '{"state":"ON", "duration": 22, "tone": "ping", "volume_level": 0.88}',
    )
    await hass.async_block_till_done()
    state3 = hass.states.get("siren.test3")
    assert state3.attributes.get(siren.ATTR_TONE) is None
    assert state3.attributes.get(siren.ATTR_DURATION) == 22
    assert state3.attributes.get(siren.ATTR_VOLUME_LEVEL) == 0.88