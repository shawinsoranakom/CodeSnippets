async def test_unloading(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
) -> None:
    """Test unloading prusalink."""
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    assert mock_config_entry.state is ConfigEntryState.LOADED

    assert hass.states.async_entity_ids_count() > 0

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED

    for state in hass.states.async_all():
        assert state.state == "unavailable"