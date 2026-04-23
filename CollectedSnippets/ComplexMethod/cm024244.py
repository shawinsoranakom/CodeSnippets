async def test_command_templates(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test siren with command templates optimistic."""
    mqtt_mock = await mqtt_mock_entry()

    state1 = hass.states.get("siren.beer")
    assert state1.state == STATE_OFF
    assert state1.attributes.get(ATTR_ASSUMED_STATE)

    state2 = hass.states.get("siren.milk")
    assert state2.state == STATE_OFF
    assert state1.attributes.get(ATTR_ASSUMED_STATE)

    await async_turn_on(
        hass,
        entity_id="siren.beer",
        parameters={
            siren.ATTR_DURATION: 22,
            siren.ATTR_TONE: "ping",
            ATTR_VOLUME_LEVEL: 0.88,
        },
    )
    state1 = hass.states.get("siren.beer")
    assert state1.attributes.get(siren.ATTR_TONE) == "ping"
    assert state1.attributes.get(siren.ATTR_DURATION) == 22
    assert state1.attributes.get(siren.ATTR_VOLUME_LEVEL) == 0.88

    mqtt_mock.async_publish.assert_any_call(
        "test-topic", "CMD: ON, DURATION: 22, TONE: ping, VOLUME: 0.88", 0, False
    )
    assert mqtt_mock.async_publish.call_count == 1
    mqtt_mock.reset_mock()
    await async_turn_off(
        hass,
        entity_id="siren.beer",
    )
    mqtt_mock.async_publish.assert_any_call(
        "test-topic", "CMD: OFF, DURATION: , TONE: , VOLUME:", 0, False
    )
    assert mqtt_mock.async_publish.call_count == 1
    mqtt_mock.reset_mock()

    await async_turn_on(
        hass,
        entity_id="siren.milk",
        parameters={
            siren.ATTR_DURATION: 22,
            siren.ATTR_TONE: "ping",
            ATTR_VOLUME_LEVEL: 0.88,
        },
    )
    state2 = hass.states.get("siren.milk")
    assert state2.attributes.get(siren.ATTR_TONE) == "ping"
    assert state2.attributes.get(siren.ATTR_DURATION) == 22
    assert state2.attributes.get(siren.ATTR_VOLUME_LEVEL) == 0.88
    await async_turn_off(
        hass,
        entity_id="siren.milk",
    )
    mqtt_mock.async_publish.assert_any_call("test-topic", "CMD_OFF: OFF", 0, False)
    assert mqtt_mock.async_publish.call_count == 2
    mqtt_mock.reset_mock()