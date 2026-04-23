async def test_rpc_polling_auth_error(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_rpc_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test RPC polling authentication error."""
    register_entity(hass, SENSOR_DOMAIN, "test_name_rssi", "wifi-rssi")
    entry = await init_integration(hass, 2)

    monkeypatch.setattr(
        mock_rpc_device,
        "poll",
        AsyncMock(
            side_effect=InvalidAuthError,
        ),
    )

    assert entry.state is ConfigEntryState.LOADED

    await mock_polling_rpc_update(hass, freezer)

    assert entry.state is ConfigEntryState.LOADED

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1

    flow = flows[0]
    assert flow.get("step_id") == "reauth_confirm"
    assert flow.get("handler") == DOMAIN

    assert "context" in flow
    assert flow["context"].get("source") == SOURCE_REAUTH
    assert flow["context"].get("entry_id") == entry.entry_id