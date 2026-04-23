async def test_update_guest_wifi_status_auth_failed(
    hass: HomeAssistant, mock_device: MockDevice
) -> None:
    """Test getting the wifi_status with wrong password triggers the reauth flow."""
    entry = configure_integration(hass)
    mock_device.device.async_get_wifi_guest_access.side_effect = DevicePasswordProtected

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