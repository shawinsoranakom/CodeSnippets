async def test_rpc_auth_error(
    hass: HomeAssistant, mock_rpc_device: Mock, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test RPC device set state authentication error."""
    mock_rpc_device.switch_set.side_effect = InvalidAuthError
    monkeypatch.delitem(mock_rpc_device.status, "cover:0")
    monkeypatch.setitem(mock_rpc_device.status["sys"], "relay_in_thermostat", False)
    entry = await init_integration(hass, 2)

    assert entry.state is ConfigEntryState.LOADED

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "switch.test_name_test_switch_0"},
        blocking=True,
    )

    assert entry.state is ConfigEntryState.LOADED

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1

    flow = flows[0]
    assert flow.get("step_id") == "reauth_confirm"
    assert flow.get("handler") == DOMAIN

    assert "context" in flow
    assert flow["context"].get("source") == SOURCE_REAUTH
    assert flow["context"].get("entry_id") == entry.entry_id