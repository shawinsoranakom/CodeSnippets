async def test_rapid_rediscover_unique(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test immediate rediscover of removed component."""
    await mqtt_mock_entry()
    events = []

    @callback
    def test_callback(event: Event) -> None:
        """Verify event got called."""
        events.append(event)

    hass.bus.async_listen(EVENT_STATE_CHANGED, test_callback)

    async_fire_mqtt_message(
        hass,
        "homeassistant/binary_sensor/bla2/config",
        '{ "name": "Ale", "state_topic": "test-topic", "unique_id": "very_unique" }',
    )
    await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.ale")
    assert state is not None
    assert len(events) == 1

    # Duplicate unique_id, immediately followed by correct unique_id
    async_fire_mqtt_message(
        hass,
        "homeassistant/binary_sensor/bla/config",
        '{ "name": "Beer", "state_topic": "test-topic", "unique_id": "very_unique" }',
    )
    async_fire_mqtt_message(
        hass,
        "homeassistant/binary_sensor/bla/config",
        '{ "name": "Beer", "state_topic": "test-topic", "unique_id": "even_uniquer" }',
    )
    # Removal, immediately followed by rediscover
    async_fire_mqtt_message(hass, "homeassistant/binary_sensor/bla/config", "")
    async_fire_mqtt_message(
        hass,
        "homeassistant/binary_sensor/bla/config",
        '{ "name": "Milk", "state_topic": "test-topic", "unique_id": "even_uniquer" }',
    )
    await hass.async_block_till_done()

    assert len(hass.states.async_entity_ids("binary_sensor")) == 2
    state = hass.states.get("binary_sensor.ale")
    assert state is not None
    state = hass.states.get("binary_sensor.beer")
    assert state is not None
    state = hass.states.get("binary_sensor.milk")
    assert state is None

    assert len(events) == 4
    # Add the entity
    assert events[1].data["entity_id"] == "binary_sensor.beer"
    assert events[1].data["old_state"] is None
    # Remove the entity
    assert events[2].data["entity_id"] == "binary_sensor.beer"
    assert events[2].data["new_state"] is None
    # Add the entity
    assert events[3].data["entity_id"] == "binary_sensor.beer"
    assert events[3].data["old_state"] is None