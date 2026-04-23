async def test_optional_door_event_sensors_from_featuremap(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    matter_client: MagicMock,
    matter_node: MatterNode,
) -> None:
    """Test discovery of optional door event sensors in doorlock featuremap."""
    entity_id_open = "sensor.mock_lock_door_open_events"
    entity_id_closed = "sensor.mock_lock_door_closed_events"

    # Check that the entities are created
    state = hass.states.get(entity_id_open)
    assert state
    assert state.state == "5"

    state = hass.states.get(entity_id_closed)
    assert state
    assert state.state == "3"

    # Test updating the sensor values
    set_node_attribute(matter_node, 1, 257, 4, 10)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get(entity_id_open)
    assert state
    assert state.state == "10"

    set_node_attribute(matter_node, 1, 257, 5, 8)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get(entity_id_closed)
    assert state
    assert state.state == "8"