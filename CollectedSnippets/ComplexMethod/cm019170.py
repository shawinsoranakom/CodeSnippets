async def test_dhcp_flow_complete_device_information(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    client: MagicMock,
    config_entry: MockConfigEntry,
    integration_setup: Callable[[MagicMock], Awaitable[bool]],
    dhcp_discovery: DhcpServiceInfo,
    appliance: HomeAppliance,
) -> None:
    """Test DHCP discovery with complete device information."""
    assert await integration_setup(client)
    assert config_entry.state is ConfigEntryState.LOADED

    device = device_registry.async_get_device(identifiers={(DOMAIN, appliance.ha_id)})
    assert device
    assert device.connections == set()

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context=ConfigFlowContext(source=config_entries.SOURCE_DHCP),
        data=dhcp_discovery,
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"

    device = device_registry.async_get_device(identifiers={(DOMAIN, appliance.ha_id)})
    assert device
    assert device.connections == {
        (dr.CONNECTION_NETWORK_MAC, dr.format_mac(dhcp_discovery.macaddress))
    }