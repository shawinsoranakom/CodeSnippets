async def test_unload_entry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_mozart_client: AsyncMock,
) -> None:
    """Test unload_entry."""

    # Load entry
    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)

    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert hasattr(mock_config_entry, "runtime_data")

    # Unload entry
    await hass.config_entries.async_unload(mock_config_entry.entry_id)

    # Ensure WebSocket notification listener and REST API client have been closed
    assert mock_mozart_client.disconnect_notifications.call_count == 1
    assert mock_mozart_client.close_api_client.call_count == 1

    # Ensure that the entry is not loaded and has been removed from hass
    assert not hasattr(mock_config_entry, "runtime_data")
    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED