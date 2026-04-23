async def test_dhcp_flow_simple(
    hass: HomeAssistant,
    mock_incomfort: MagicMock,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test dhcp flow for older gateway without authentication needed.

    Assert on the creation of the gateway device, climate and boiler devices.
    """
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=DHCP_SERVICE_INFO
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "dhcp_confirm"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {"host": "192.168.1.12"}

    config_entry: ConfigEntry = result["result"]
    entry_id = config_entry.entry_id

    await hass.async_block_till_done(wait_background_tasks=True)

    # Check the gateway device is discovered
    gateway_device = device_registry.async_get_device(identifiers={(DOMAIN, entry_id)})
    assert gateway_device is not None
    assert gateway_device.name == "RFGateway"
    assert gateway_device.manufacturer == "Intergas"
    assert gateway_device.connections == {("mac", "00:04:a3:de:ad:ff")}

    devices = device_registry.devices.get_devices_for_config_entry_id(entry_id)
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

    # Check the host is dynamically updated
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=DHCP_SERVICE_INFO_ALT
    )
    await hass.async_block_till_done(wait_background_tasks=True)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert config_entry.data[CONF_HOST] == DHCP_SERVICE_INFO_ALT.ip