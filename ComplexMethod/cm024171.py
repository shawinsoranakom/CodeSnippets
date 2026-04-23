async def test_discovery_component_availability_overridden(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    discovery_topic: str,
    payload: str,
) -> None:
    """Test device discovery with overridden shared availability mapping."""
    await mqtt_mock_entry()
    async_fire_mqtt_message(
        hass,
        discovery_topic,
        payload,
    )
    await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.beer")
    assert state is not None
    assert state.name == "Beer"
    assert state.state == STATE_UNAVAILABLE

    async_fire_mqtt_message(
        hass,
        "avty-topic-device",
        "online",
    )
    await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.beer")
    assert state is not None
    assert state.state == STATE_UNAVAILABLE

    async_fire_mqtt_message(
        hass,
        "avty-topic-component",
        "online",
    )
    await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.beer")
    assert state is not None
    assert state.state == STATE_UNKNOWN

    async_fire_mqtt_message(
        hass,
        "test-topic",
        "ON",
    )
    await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.beer")
    assert state is not None
    assert state.state == STATE_ON