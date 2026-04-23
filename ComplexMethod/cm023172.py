async def test_legacy_door_state_entities_follow_opening_state(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    client,
    hoppe_ehandle_connectsense_state,
) -> None:
    """Test all legacy door state entities correctly derive state from Opening state."""
    node = Node(client, hoppe_ehandle_connectsense_state)
    client.driver.controller.nodes[node.node_id] = node

    entry = MockConfigEntry(domain="zwave_js", data={"url": "ws://test.org"})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # Re-enable all 6 legacy door state entities.
    legacy_names = {
        "Window/door is open",
        "Window/door is closed",
        "Window/door is open in regular position",
        "Window/door is open in tilt position",
    }
    legacy_entries = [
        e
        for e in entity_registry.entities.values()
        if e.domain == "binary_sensor"
        and e.platform == "zwave_js"
        and e.original_name in legacy_names
    ]
    assert len(legacy_entries) == 6
    for legacy_entry in legacy_entries:
        entity_registry.async_update_entity(legacy_entry.entity_id, disabled_by=None)

    async_fire_time_changed(
        hass,
        dt_util.utcnow() + timedelta(seconds=RELOAD_AFTER_UPDATE_DELAY + 1),
    )
    await hass.async_block_till_done()

    # With Opening state = 0 (Closed), all "open" entities should be OFF and
    # all "closed" entities should be ON.
    open_entries = [
        e for e in legacy_entries if e.original_name == "Window/door is open"
    ]
    closed_entries = [
        e for e in legacy_entries if e.original_name == "Window/door is closed"
    ]
    open_regular_entries = [
        e
        for e in legacy_entries
        if e.original_name == "Window/door is open in regular position"
    ]
    open_tilt_entries = [
        e
        for e in legacy_entries
        if e.original_name == "Window/door is open in tilt position"
    ]

    for e in open_entries + open_regular_entries + open_tilt_entries:
        state = hass.states.get(e.entity_id)
        assert state, f"{e.entity_id} should have a state"
        assert state.state == STATE_OFF, (
            f"{e.entity_id} ({e.original_name}) should be OFF when Opening state=Closed"
        )
    for e in closed_entries:
        state = hass.states.get(e.entity_id)
        assert state, f"{e.entity_id} should have a state"
        assert state.state == STATE_ON, (
            f"{e.entity_id} ({e.original_name}) should be ON when Opening state=Closed"
        )

    # Update Opening state to 1 (Open).
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
                    "newValue": 1,
                    "prevValue": 0,
                    "propertyName": "Access Control",
                    "propertyKeyName": "Opening state",
                },
            },
        )
    )
    await hass.async_block_till_done()

    # All "open" entities should now be ON, "closed" OFF, "tilt" OFF.
    for e in open_entries + open_regular_entries:
        state = hass.states.get(e.entity_id)
        assert state, f"{e.entity_id} should have a state"
        assert state.state == STATE_ON, (
            f"{e.entity_id} ({e.original_name}) should be ON when Opening state=Open"
        )
    for e in closed_entries + open_tilt_entries:
        state = hass.states.get(e.entity_id)
        assert state, f"{e.entity_id} should have a state"
        assert state.state == STATE_OFF, (
            f"{e.entity_id} ({e.original_name}) should be OFF when Opening state=Open"
        )