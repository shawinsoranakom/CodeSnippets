async def test_rapid_reconfigure(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test immediate reconfigure of added component."""
    await mqtt_mock_entry()
    events = []

    @callback
    def test_callback(event: Event) -> None:
        """Verify event got called."""
        events.append(event)

    hass.bus.async_listen(EVENT_STATE_CHANGED, test_callback)

    # Discovery immediately followed by reconfig
    async_fire_mqtt_message(hass, "homeassistant/binary_sensor/bla/config", "")
    async_fire_mqtt_message(
        hass,
        "homeassistant/binary_sensor/bla/config",
        '{ "name": "Beer", "state_topic": "test-topic1" }',
    )
    async_fire_mqtt_message(
        hass,
        "homeassistant/binary_sensor/bla/config",
        '{ "name": "Milk", "state_topic": "test-topic2" }',
    )
    async_fire_mqtt_message(
        hass,
        "homeassistant/binary_sensor/bla/config",
        '{ "name": "Wine", "state_topic": "test-topic3" }',
    )
    await hass.async_block_till_done()

    assert len(hass.states.async_entity_ids("binary_sensor")) == 1
    state = hass.states.get("binary_sensor.beer")
    assert state is not None

    assert len(events) == 3
    # Add the entity
    assert events[0].data["entity_id"] == "binary_sensor.beer"
    assert events[0].data["old_state"] is None
    assert events[0].data["new_state"].attributes["friendly_name"] == "Beer"
    # Update the entity
    assert events[1].data["entity_id"] == "binary_sensor.beer"
    assert events[1].data["new_state"] is not None
    assert events[1].data["old_state"] is not None
    assert events[1].data["new_state"].attributes["friendly_name"] == "Milk"
    # Update the entity
    assert events[2].data["entity_id"] == "binary_sensor.beer"
    assert events[2].data["new_state"] is not None
    assert events[2].data["old_state"] is not None
    assert events[2].data["new_state"].attributes["friendly_name"] == "Wine"