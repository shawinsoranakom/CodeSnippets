async def test_filtering_not_supported_attributes_optimistic(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test setting attributes with support flags optimistic."""
    await mqtt_mock_entry()

    state1 = hass.states.get("siren.test1")
    assert state1.state == STATE_OFF
    assert siren.ATTR_DURATION not in state1.attributes
    assert siren.ATTR_AVAILABLE_TONES in state1.attributes
    assert siren.ATTR_TONE in state1.attributes
    assert siren.ATTR_VOLUME_LEVEL in state1.attributes
    await async_turn_on(
        hass,
        entity_id="siren.test1",
        parameters={
            siren.ATTR_DURATION: 22,
            siren.ATTR_TONE: "ping",
            ATTR_VOLUME_LEVEL: 0.88,
        },
    )
    state1 = hass.states.get("siren.test1")
    assert state1.attributes.get(siren.ATTR_TONE) == "ping"
    assert state1.attributes.get(siren.ATTR_DURATION) is None
    assert state1.attributes.get(siren.ATTR_VOLUME_LEVEL) == 0.88

    state2 = hass.states.get("siren.test2")
    assert siren.ATTR_DURATION in state2.attributes
    assert siren.ATTR_AVAILABLE_TONES in state2.attributes
    assert siren.ATTR_TONE in state2.attributes
    assert siren.ATTR_VOLUME_LEVEL not in state2.attributes
    await async_turn_on(
        hass,
        entity_id="siren.test2",
        parameters={
            siren.ATTR_DURATION: 22,
            siren.ATTR_TONE: "ping",
            ATTR_VOLUME_LEVEL: 0.88,
        },
    )
    state2 = hass.states.get("siren.test2")
    assert state2.attributes.get(siren.ATTR_TONE) == "ping"
    assert state2.attributes.get(siren.ATTR_DURATION) == 22
    assert state2.attributes.get(siren.ATTR_VOLUME_LEVEL) is None

    state3 = hass.states.get("siren.test3")
    assert siren.ATTR_DURATION in state3.attributes
    assert siren.ATTR_AVAILABLE_TONES not in state3.attributes
    assert siren.ATTR_TONE not in state3.attributes
    assert siren.ATTR_VOLUME_LEVEL in state3.attributes
    await async_turn_on(
        hass,
        entity_id="siren.test3",
        parameters={
            siren.ATTR_DURATION: 22,
            siren.ATTR_TONE: "ping",
            ATTR_VOLUME_LEVEL: 0.88,
        },
    )
    state3 = hass.states.get("siren.test3")
    assert state3.attributes.get(siren.ATTR_TONE) is None
    assert state3.attributes.get(siren.ATTR_DURATION) == 22
    assert state3.attributes.get(siren.ATTR_VOLUME_LEVEL) == 0.88