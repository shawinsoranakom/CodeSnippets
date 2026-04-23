async def test_discovered_by_dhcp_does_not_update_if_already_loaded(
    hass: HomeAssistant, device_registry: dr.DeviceRegistry
) -> None:
    """Test dhcp does not update existing host if its already loaded."""
    config_entry, _camera, device = await setup_onvif_integration(hass)
    device.profiles = device.async_get_profiles()
    devices = dr.async_entries_for_config_entry(device_registry, config_entry.entry_id)
    assert len(devices) == 1
    device = devices[0]
    assert device.model == "TestModel"
    assert device.connections == {(dr.CONNECTION_NETWORK_MAC, MAC)}
    assert config_entry.data[CONF_HOST] == "1.2.3.4"

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=DHCP_DISCOVERY
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert config_entry.data[CONF_HOST] != DHCP_DISCOVERY.ip