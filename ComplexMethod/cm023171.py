async def test_reenabled_legacy_door_state_entity_follows_opening_state(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    client,
    hoppe_ehandle_connectsense_state,
) -> None:
    """Test a re-enabled legacy Door state entity derives state from Opening state."""
    node = Node(client, hoppe_ehandle_connectsense_state)
    client.driver.controller.nodes[node.node_id] = node

    entry = MockConfigEntry(domain="zwave_js", data={"url": "ws://test.org"})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    legacy_entry = next(
        entry
        for entry in entity_registry.entities.values()
        if entry.platform == "zwave_js"
        and entry.original_name == "Window/door is open in tilt position"
    )

    entity_registry.async_update_entity(legacy_entry.entity_id, disabled_by=None)
    async_fire_time_changed(
        hass,
        dt_util.utcnow() + timedelta(seconds=RELOAD_AFTER_UPDATE_DELAY + 1),
    )
    await hass.async_block_till_done()

    state = hass.states.get(legacy_entry.entity_id)
    assert state
    assert state.state == STATE_OFF

    node.receive_event(
        Event(
            type="value updated",
            data={
                "source": "node",
                "event": "value updated",
                "nodeId": node.node_id,
                "args": {
                    "commandClassName": "Notification",
                    "commandClass": 113,
                    "endpoint": 0,
                    "property": "Access Control",
                    "propertyKey": "Opening state",
                    "newValue": 2,
                    "prevValue": 0,
                    "propertyName": "Access Control",
                    "propertyKeyName": "Opening state",
                },
            },
        )
    )

    state = hass.states.get(legacy_entry.entity_id)
    assert state
    assert state.state == STATE_ON