async def test_rpc_reconnect_auth_error(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_rpc_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test RPC reconnect authentication error."""
    entry = await init_integration(hass, 2)

    monkeypatch.setattr(mock_rpc_device, "connected", False)
    monkeypatch.setattr(
        mock_rpc_device,
        "initialize",
        AsyncMock(
            side_effect=InvalidAuthError,
        ),
    )

    assert entry.state is ConfigEntryState.LOADED

    # Move time to generate reconnect
    freezer.tick(timedelta(seconds=RPC_RECONNECT_INTERVAL))
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