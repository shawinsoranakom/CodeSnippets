async def test_valve_setup(
    hass: HomeAssistant,
    mock_config_entry: tuple[MockConfigEntry, list[ValveEntity]],
    snapshot: SnapshotAssertion,
) -> None:
    """Test setup and tear down of valve platform and entity."""
    config_entry = mock_config_entry[0]

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED
    for entity in mock_config_entry[1]:
        entity_id = entity.entity_id
        state = hass.states.get(entity_id)
        assert state
        assert state == snapshot

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.NOT_LOADED

    for entity in mock_config_entry[1]:
        entity_id = entity.entity_id
        state = hass.states.get(entity_id)
        assert state
        assert state.state == STATE_UNAVAILABLE
        assert state == snapshot