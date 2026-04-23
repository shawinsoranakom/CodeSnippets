async def test_fix_unique_id(
    hass: HomeAssistant,
    responses: list[AiohttpClientMockResponse],
    config_entry: MockConfigEntry,
) -> None:
    """Test fix of a config entry with no unique id."""

    responses.insert(1, mock_json_response(WIFI_PARAMS_RESPONSE))

    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    assert entries[0].state is ConfigEntryState.NOT_LOADED
    assert entries[0].unique_id is None
    assert entries[0].data.get(CONF_MAC) is None

    await hass.config_entries.async_setup(config_entry.entry_id)
    assert config_entry.state is ConfigEntryState.LOADED

    # Verify config entry now has a unique id
    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    assert entries[0].state is ConfigEntryState.LOADED
    assert entries[0].unique_id == MAC_ADDRESS_UNIQUE_ID
    assert entries[0].data.get(CONF_MAC) == MAC_ADDRESS