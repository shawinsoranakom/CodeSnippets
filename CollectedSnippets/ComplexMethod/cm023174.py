async def test_access_control_lock_state_notification_sensors(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    client,
    lock_august_asl03_state,
) -> None:
    """Test Access Control lock state notification sensors from new discovery schemas."""
    node = Node(client, _add_lock_state_notification_states(lock_august_asl03_state))
    client.driver.controller.nodes[node.node_id] = node

    entry = MockConfigEntry(domain="zwave_js", data={"url": "ws://test.org"})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    lock_state_entities = [
        state
        for state in hass.states.async_all("binary_sensor")
        if state.attributes.get(ATTR_DEVICE_CLASS) == BinarySensorDeviceClass.LOCK
    ]
    assert len(lock_state_entities) == 4
    assert all(state.state == STATE_OFF for state in lock_state_entities)

    jammed_entry = next(
        entry
        for entry in entity_registry.entities.values()
        if entry.domain == "binary_sensor"
        and entry.platform == "zwave_js"
        and entry.original_name == "Lock jammed"
    )
    assert jammed_entry.original_device_class == BinarySensorDeviceClass.PROBLEM
    assert jammed_entry.entity_category == EntityCategory.DIAGNOSTIC

    jammed_state = hass.states.get(jammed_entry.entity_id)
    assert jammed_state
    assert jammed_state.state == STATE_OFF