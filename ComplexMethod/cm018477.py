async def test_blu_trv_set_target_temp_auth_error(
    hass: HomeAssistant,
    mock_blu_trv: Mock,
) -> None:
    """BLU TRV target temperature setting test with authentication error."""
    entry = await init_integration(hass, 3, model=MODEL_BLU_GATEWAY_G3)

    mock_blu_trv.blu_trv_set_target_temperature.side_effect = InvalidAuthError

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {ATTR_ENTITY_ID: "climate.trv_name", ATTR_TEMPERATURE: 28},
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