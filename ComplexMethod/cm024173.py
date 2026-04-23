async def test_rapid_rediscover(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test immediate rediscover of removed component."""
    await mqtt_mock_entry()
    events = async_capture_events(hass, EVENT_STATE_CHANGED)

    async_fire_mqtt_message(
        hass,
        "homeassistant/binary_sensor/bla/config",
        '{ "name": "Beer", "state_topic": "test-topic" }',
    )
    await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.beer")
    assert state is not None
    assert len(events) == 1

    # Removal immediately followed by rediscover
    async_fire_mqtt_message(hass, "homeassistant/binary_sensor/bla/config", "")
    async_fire_mqtt_message(
        hass,
        "homeassistant/binary_sensor/bla/config",
        '{ "name": "Beer", "state_topic": "test-topic" }',
    )
    async_fire_mqtt_message(hass, "homeassistant/binary_sensor/bla/config", "")
    async_fire_mqtt_message(
        hass,
        "homeassistant/binary_sensor/bla/config",
        '{ "name": "Milk", "state_topic": "test-topic" }',
    )
    await hass.async_block_till_done()

    assert len(hass.states.async_entity_ids("binary_sensor")) == 1
    state = hass.states.get("binary_sensor.milk")
    assert state is not None

    assert len(events) == 5
    # Remove the entity
    assert events[1].data["entity_id"] == "binary_sensor.beer"
    assert events[1].data["new_state"] is None
    # Add the entity
    assert events[2].data["entity_id"] == "binary_sensor.beer"
    assert events[2].data["old_state"] is None
    # Remove the entity
    assert events[3].data["entity_id"] == "binary_sensor.beer"
    assert events[3].data["new_state"] is None
    # Add the entity
    assert events[4].data["entity_id"] == "binary_sensor.milk"
    assert events[4].data["old_state"] is None