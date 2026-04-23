async def test_node_status_sensor_not_ready(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    client,
    lock_id_lock_as_id150_not_ready,
    lock_id_lock_as_id150_state,
    integration,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test node status sensor is created and available if node is not ready."""
    node_status_entity_id = "sensor.z_wave_module_for_id_lock_150_and_101_node_status"
    node = lock_id_lock_as_id150_not_ready
    assert not node.ready
    entity_entry = entity_registry.async_get(node_status_entity_id)

    assert not entity_entry.disabled
    assert hass.states.get(node_status_entity_id)
    assert hass.states.get(node_status_entity_id).state == "alive"

    # Mark node as ready
    event = Event(
        "ready",
        {
            "source": "node",
            "event": "ready",
            "nodeId": node.node_id,
            "nodeState": lock_id_lock_as_id150_state,
        },
    )
    node.receive_event(event)
    assert node.ready
    assert hass.states.get(node_status_entity_id)
    assert hass.states.get(node_status_entity_id).state == "alive"

    await hass.services.async_call(
        DOMAIN,
        SERVICE_REFRESH_VALUE,
        {
            ATTR_ENTITY_ID: node_status_entity_id,
        },
        blocking=True,
    )
    await hass.async_block_till_done()
    assert "There is no value to refresh for this entity" in caplog.text