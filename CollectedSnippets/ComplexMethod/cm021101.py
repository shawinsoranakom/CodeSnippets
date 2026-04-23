async def test_setup_failed_update_reauth(
    hass: HomeAssistant, ufp: MockUFPFixture
) -> None:
    """Test setup of unifiprotect entry with update that gives unauthroized error."""

    await hass.config_entries.async_setup(ufp.entry.entry_id)
    await hass.async_block_till_done()
    assert ufp.entry.state is ConfigEntryState.LOADED

    # reauth should not be triggered until there are 10 auth failures in a row
    # to verify it is not transient
    ufp.api.update = AsyncMock(side_effect=NotAuthorized)
    for _ in range(AUTH_RETRIES):
        await time_changed(hass, DEVICE_UPDATE_INTERVAL)
        assert len(hass.config_entries.flow._progress) == 0

    assert ufp.api.update.call_count == AUTH_RETRIES
    assert ufp.entry.state is ConfigEntryState.LOADED

    await time_changed(hass, DEVICE_UPDATE_INTERVAL)
    assert ufp.api.update.call_count == AUTH_RETRIES + 1
    assert len(hass.config_entries.flow._progress) == 1