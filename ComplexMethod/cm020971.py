async def test_bridge_api_call_reauth(
    hass: HomeAssistant,
    mock_serial_bridge: AsyncMock,
    mock_serial_bridge_config_entry: MockConfigEntry,
) -> None:
    """Test bridge_api_call decorator for reauth."""

    await setup_integration(hass, mock_serial_bridge_config_entry)

    assert (state := hass.states.get(ENTITY_ID_0))
    assert state.state == STATE_OFF

    mock_serial_bridge.set_device_status.side_effect = CannotAuthenticate

    # Call API
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY_ID_0},
        blocking=True,
    )

    assert mock_serial_bridge_config_entry.state is ConfigEntryState.LOADED

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1

    flow = flows[0]
    assert flow.get("step_id") == "reauth_confirm"
    assert flow.get("handler") == DOMAIN

    assert "context" in flow
    assert flow["context"].get("source") == SOURCE_REAUTH
    assert flow["context"].get("entry_id") == mock_serial_bridge_config_entry.entry_id