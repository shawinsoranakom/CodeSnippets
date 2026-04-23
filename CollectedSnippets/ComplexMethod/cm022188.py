async def test_setup(
    hass: HomeAssistant, connection, config_entry: MockConfigEntry, model: str
) -> None:
    """Test load and unload."""
    with patch(MOCKED_MODEL, return_value=model) as mock:
        await hass.config_entries.async_setup(config_entry.entry_id)
        assert await async_setup_component(hass, DOMAIN, {})
    assert config_entry.state is ConfigEntryState.LOADED
    assert mock.called

    with patch(MOCKED_MODEL, return_value=model) as mock:
        assert await hass.config_entries.async_unload(config_entry.entry_id)
        await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.NOT_LOADED
    assert not hass.data.get(DOMAIN)
    assert mock.called