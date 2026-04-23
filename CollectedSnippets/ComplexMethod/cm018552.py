async def test_blu_trv_number_reauth_error(
    hass: HomeAssistant,
    mock_blu_trv: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test RPC/BLU TRV number with authentication error."""
    entry = await init_integration(hass, 3, model=MODEL_BLU_GATEWAY_G3)

    mock_blu_trv.blu_trv_set_external_temperature.side_effect = InvalidAuthError

    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {
            ATTR_ENTITY_ID: f"{NUMBER_DOMAIN}.trv_name_external_temperature",
            ATTR_VALUE: 20.0,
        },
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