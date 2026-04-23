async def test_button_press_auth_error(hass: HomeAssistant) -> None:
    """Test button press when auth error occurs."""
    entry = await init_integration(hass)

    with patch(
        "homeassistant.components.nam.NettigoAirMonitor.async_restart",
        side_effect=AuthFailedError("auth error"),
    ):
        await hass.services.async_call(
            BUTTON_DOMAIN,
            SERVICE_PRESS,
            {ATTR_ENTITY_ID: "button.nettigo_air_monitor_restart"},
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