async def test_update_last_update_auth_failed(
    hass: HomeAssistant, mock_device: MockDevice
) -> None:
    """Test getting the last update state with wrong password triggers the reauth flow."""
    entry = configure_integration(hass)
    mock_device.device.async_uptime.side_effect = DevicePasswordProtected

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_ERROR

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1

    flow = flows[0]
    assert flow["step_id"] == "reauth_confirm"
    assert flow["handler"] == DOMAIN

    assert "context" in flow
    assert flow["context"]["source"] == SOURCE_REAUTH
    assert flow["context"]["entry_id"] == entry.entry_id