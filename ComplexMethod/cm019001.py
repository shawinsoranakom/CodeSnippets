async def test_auth_failed(hass: HomeAssistant, mock_device: MockDevice) -> None:
    """Test updating unauthorized triggers the reauth flow."""
    entry = configure_integration(hass)
    device_name = entry.title.replace(" ", "_").lower()
    entity_id = f"{UPDATE_DOMAIN}.{device_name}_firmware"

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    mock_device.device.async_start_firmware_update.side_effect = DevicePasswordProtected

    with pytest.raises(HomeAssistantError):
        assert await hass.services.async_call(
            UPDATE_DOMAIN,
            SERVICE_INSTALL,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
    await hass.async_block_till_done()
    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1

    flow = flows[0]
    assert flow["step_id"] == "reauth_confirm"
    assert flow["handler"] == DOMAIN
    assert "context" in flow
    assert flow["context"]["source"] == SOURCE_REAUTH
    assert flow["context"]["entry_id"] == entry.entry_id