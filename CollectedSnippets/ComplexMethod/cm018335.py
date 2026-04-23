async def test_async_setup_multiple_entries(
    hass: HomeAssistant, entry: MockConfigEntry, entry2
) -> None:
    """Test a successful setup and unload of multiple entries."""
    hass.http = Mock()
    with patch(
        "homeassistant.components.lcn.PchkConnectionManager", MockPchkConnectionManager
    ):
        for config_entry in (entry, entry2):
            await init_integration(hass, config_entry)
            assert config_entry.state is ConfigEntryState.LOADED

    assert len(hass.config_entries.async_entries(DOMAIN)) == 2

    for config_entry in (entry, entry2):
        assert await hass.config_entries.async_unload(config_entry.entry_id)
        await hass.async_block_till_done()

        assert config_entry.state is ConfigEntryState.NOT_LOADED

    assert not hass.data.get(DOMAIN)