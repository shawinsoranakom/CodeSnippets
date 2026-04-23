async def test_access_control_catch_all_with_opening_state_present(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    client,
    hoppe_ehandle_connectsense_state,
) -> None:
    """Test that unrelated Access Control values are discovered even when Opening state is present."""
    node = Node(
        client,
        _add_barrier_status_value(hoppe_ehandle_connectsense_state),
    )
    client.driver.controller.nodes[node.node_id] = node

    entry = MockConfigEntry(domain="zwave_js", data={"url": "ws://test.org"})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # The two non-idle barrier states should each become a diagnostic binary sensor
    barrier_entries = [
        reg_entry
        for reg_entry in entity_registry.entities.values()
        if reg_entry.domain == "binary_sensor"
        and reg_entry.platform == "zwave_js"
        and reg_entry.entity_category == EntityCategory.DIAGNOSTIC
        and reg_entry.original_name
        and "barrier" in reg_entry.original_name.lower()
    ]
    assert len(barrier_entries) == 2, (
        f"Expected 2 barrier status sensors, got {[e.original_name for e in barrier_entries]}"
    )
    for reg_entry in barrier_entries:
        state = hass.states.get(reg_entry.entity_id)
        assert state is not None
        assert state.state == STATE_OFF