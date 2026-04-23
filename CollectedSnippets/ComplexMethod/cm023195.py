async def test_node_status_sensor(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    client,
    lock_id_lock_as_id150,
    integration,
) -> None:
    """Test node status sensor is created and gets updated on node state changes."""
    node_status_entity_id = "sensor.z_wave_module_for_id_lock_150_and_101_node_status"
    node = lock_id_lock_as_id150
    entity_entry = entity_registry.async_get(node_status_entity_id)

    assert not entity_entry.disabled
    assert entity_entry.entity_category is EntityCategory.DIAGNOSTIC
    assert hass.states.get(node_status_entity_id).state == "alive"

    # Test transitions work
    event = Event(
        "dead", data={"source": "node", "event": "dead", "nodeId": node.node_id}
    )
    node.receive_event(event)
    assert hass.states.get(node_status_entity_id).state == "dead"

    event = Event(
        "wake up", data={"source": "node", "event": "wake up", "nodeId": node.node_id}
    )
    node.receive_event(event)
    assert hass.states.get(node_status_entity_id).state == "awake"

    event = Event(
        "sleep", data={"source": "node", "event": "sleep", "nodeId": node.node_id}
    )
    node.receive_event(event)
    assert hass.states.get(node_status_entity_id).state == "asleep"

    event = Event(
        "alive", data={"source": "node", "event": "alive", "nodeId": node.node_id}
    )
    node.receive_event(event)
    assert hass.states.get(node_status_entity_id).state == "alive"

    # Disconnect the client and make sure the entity is still available
    await client.disconnect()
    assert hass.states.get(node_status_entity_id).state != STATE_UNAVAILABLE

    # Assert a node status sensor entity is not created for the controller
    driver = client.driver
    node = driver.controller.nodes[1]
    assert node.is_controller_node
    assert (
        entity_registry.async_get_entity_id(
            DOMAIN,
            "sensor",
            f"{get_valueless_base_unique_id(driver, node)}.node_status",
        )
        is None
    )

    # Assert a controller status sensor entity is not created for a node
    assert (
        entity_registry.async_get_entity_id(
            DOMAIN,
            "sensor",
            f"{get_valueless_base_unique_id(driver, node)}.controller_status",
        )
        is None
    )