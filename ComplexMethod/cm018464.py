async def test_device_auth_error(
    hass: HomeAssistant,
    gen: int,
    mock_block_device: Mock,
    mock_rpc_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test device authentication error."""
    monkeypatch.setattr(
        mock_block_device, "initialize", AsyncMock(side_effect=InvalidAuthError)
    )
    monkeypatch.setattr(
        mock_rpc_device, "initialize", AsyncMock(side_effect=InvalidAuthError)
    )

    entry = await init_integration(hass, gen)
    assert entry.state is ConfigEntryState.SETUP_ERROR

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1

    flow = flows[0]
    assert flow.get("step_id") == "reauth_confirm"
    assert flow.get("handler") == DOMAIN

    assert "context" in flow
    assert flow["context"].get("source") == SOURCE_REAUTH
    assert flow["context"].get("entry_id") == entry.entry_id