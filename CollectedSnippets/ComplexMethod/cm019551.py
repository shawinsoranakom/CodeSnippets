async def test_entry_setup_unload(
    hass: HomeAssistant,
    matter_client: MagicMock,
) -> None:
    """Test the integration set up and unload."""
    node = create_node_from_fixture("mock_onoff_light")
    matter_client.get_nodes.return_value = [node]
    matter_client.get_node.return_value = node
    entry = MockConfigEntry(domain="matter", data={"url": "ws://localhost:5580/ws"})
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert matter_client.connect.call_count == 1
    assert matter_client.set_default_fabric_label.call_count == 1
    assert entry.state is ConfigEntryState.LOADED
    entity_state = hass.states.get("light.mock_onoff_light")
    assert entity_state
    assert entity_state.state != STATE_UNAVAILABLE

    await hass.config_entries.async_unload(entry.entry_id)

    assert matter_client.disconnect.call_count == 1
    assert entry.state is ConfigEntryState.NOT_LOADED
    entity_state = hass.states.get("light.mock_onoff_light")
    assert entity_state
    assert entity_state.state == STATE_UNAVAILABLE