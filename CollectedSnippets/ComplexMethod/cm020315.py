async def test_integration_unloaded(
    hass: HomeAssistant, auth: FakeAuth, setup_platform
) -> None:
    """Test the media player loads, but has no devices, when config unloaded."""
    await setup_platform()

    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}")
    assert browse.domain == DOMAIN
    assert browse.identifier == ""
    assert browse.title == "Nest"
    assert len(browse.children) == 1

    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    entry = entries[0]
    assert entry.state is ConfigEntryState.LOADED

    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is ConfigEntryState.NOT_LOADED

    # No devices returned
    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}")
    assert browse.domain == DOMAIN
    assert browse.identifier == ""
    assert browse.title == "Nest"
    assert len(browse.children) == 0