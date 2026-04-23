async def test_unload_entry(
    hass: HomeAssistant,
    setup_entry: MockConfigEntry,
    device_manager: AsyncMock,
) -> None:
    """Test unloading roborock integration."""
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    assert setup_entry.state is ConfigEntryState.LOADED

    assert device_manager.get_devices.called
    assert not device_manager.close.called

    # Unload the config entry and verify that the device manager is closed
    assert await hass.config_entries.async_unload(setup_entry.entry_id)
    await hass.async_block_till_done()
    assert setup_entry.state is ConfigEntryState.NOT_LOADED

    assert device_manager.close.called