async def test_rpc_blu_trv_button_auth_error(
    hass: HomeAssistant,
    mock_blu_trv: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test RPC BLU TRV button with authentication error."""
    monkeypatch.delitem(mock_blu_trv.status, "script:1")
    monkeypatch.delitem(mock_blu_trv.status, "script:2")
    monkeypatch.delitem(mock_blu_trv.status, "script:3")

    entry = await init_integration(hass, 3, model=MODEL_BLU_GATEWAY_G3)

    mock_blu_trv.trigger_blu_trv_calibration.side_effect = InvalidAuthError

    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: "button.trv_name_calibrate"},
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