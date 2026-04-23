async def test_dhcp_flow_migrates_existing_entry_without_unique_id(
    hass: HomeAssistant,
    mock_incomfort: MagicMock,
    mock_config_entry: MockConfigEntry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test dhcp flow migrates an existing entry without unique_id."""
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=DHCP_SERVICE_INFO
    )
    await hass.async_block_till_done(wait_background_tasks=True)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"

    # Check the gateway device is discovered after a reload
    # And has updated connections
    gateway_device = device_registry.async_get_device(
        identifiers={(DOMAIN, mock_config_entry.entry_id)}
    )
    assert gateway_device is not None
    assert gateway_device.name == "RFGateway"
    assert gateway_device.manufacturer == "Intergas"
    assert gateway_device.connections == {("mac", "00:04:a3:de:ad:ff")}

    devices = device_registry.devices.get_devices_for_config_entry_id(
        mock_config_entry.entry_id
    )
    assert len(devices) == 3
    boiler_device = device_registry.async_get_device(
        identifiers={(DOMAIN, "c0ffeec0ffee")}
    )
    assert boiler_device.via_device_id == gateway_device.id
    assert boiler_device is not None
    climate_device = device_registry.async_get_device(
        identifiers={(DOMAIN, "c0ffeec0ffee_1")}
    )
    assert climate_device is not None
    assert climate_device.via_device_id == gateway_device.id