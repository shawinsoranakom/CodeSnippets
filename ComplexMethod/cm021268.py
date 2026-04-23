async def test_setup_success(
    hass: HomeAssistant,
    setup_integration: ComponentSetup,
    config_entry: MockConfigEntry,
) -> None:
    """Test successful setup, unload, and re-setup."""
    # Initial setup
    await setup_integration()
    assert config_entry.state is ConfigEntryState.LOADED
    assert hass.services.has_service(DOMAIN, "send_text_command")

    # Unload the entry
    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()
    assert not hass.data.get(DOMAIN)
    assert config_entry.state is ConfigEntryState.NOT_LOADED
    assert hass.services.has_service(DOMAIN, "send_text_command")

    # Re-setup the entry
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.LOADED
    assert hass.services.has_service(DOMAIN, "send_text_command")