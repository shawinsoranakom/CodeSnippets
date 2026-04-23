async def test_block_polling_auth_error(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_block_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test block device polling authentication error."""
    monkeypatch.setattr(
        mock_block_device,
        "update",
        AsyncMock(side_effect=InvalidAuthError),
    )
    entry = await init_integration(hass, 1)

    assert entry.state is ConfigEntryState.LOADED

    # Move time to generate polling
    freezer.tick(timedelta(seconds=UPDATE_PERIOD_MULTIPLIER * 15))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1

    flow = flows[0]
    assert flow.get("step_id") == "reauth_confirm"
    assert flow.get("handler") == DOMAIN

    assert "context" in flow
    assert flow["context"].get("source") == SOURCE_REAUTH
    assert flow["context"].get("entry_id") == entry.entry_id