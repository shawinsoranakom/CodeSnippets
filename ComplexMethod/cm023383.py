async def test_trophy_title_coordinator_auth_failed(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_psnawpapi: MagicMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test trophy title coordinator starts reauth on authentication error."""

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED

    mock_psnawpapi.user.return_value.trophy_titles.side_effect = (
        PSNAWPAuthenticationError("error msg")
    )

    freezer.tick(timedelta(days=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)
    await hass.async_block_till_done(wait_background_tasks=True)

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1

    flow = flows[0]
    assert flow.get("step_id") == "reauth_confirm"
    assert flow.get("handler") == DOMAIN

    assert "context" in flow
    assert flow["context"].get("source") == SOURCE_REAUTH
    assert flow["context"].get("entry_id") == config_entry.entry_id