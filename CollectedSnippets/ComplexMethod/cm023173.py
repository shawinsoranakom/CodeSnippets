async def test_legacy_door_state_non_zero_endpoint(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    client: MagicMock,
    hoppe_ehandle_connectsense_state: NodeDataType,
) -> None:
    """Test legacy door state entities work when notification values are on endpoint 1.

    Regression test for https://github.com/home-assistant/core/issues/166365.
    """
    state = _move_notification_values_to_endpoint(
        hoppe_ehandle_connectsense_state, endpoint=1
    )
    node = Node(client, state)
    client.driver.controller.nodes[node.node_id] = node

    entry = MockConfigEntry(domain="zwave_js", data={"url": "ws://test.org"})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # Legacy door state entities should still be discovered and disabled by default
    # (because the Opening state value exists on the same endpoint).
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

    # Re-enable them to verify they can be initialized without errors.
    for legacy_entry in legacy_entries:
        entity_registry.async_update_entity(legacy_entry.entity_id, disabled_by=None)

    async_fire_time_changed(
        hass,
        dt_util.utcnow() + timedelta(seconds=RELOAD_AFTER_UPDATE_DELAY + 1),
    )
    await hass.async_block_till_done()

    # All entities should have a valid state (no assertion errors during init).
    for e in legacy_entries:
        state = hass.states.get(e.entity_id)
        assert state is not None, f"{e.entity_id} should have a state"
        assert state.state != STATE_UNKNOWN, (
            f"{e.entity_id} ({e.original_name}) should not be unknown"
        )