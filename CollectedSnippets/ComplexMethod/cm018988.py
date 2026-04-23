async def test_sensor_setup(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test default setup of the sensor component."""
    entry = configure_integration(hass)
    device_name = entry.title.replace(" ", "_").lower()
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED

    assert not entity_registry.async_get(
        f"{SENSOR_DOMAIN}.{device_name}_connected_wi_fi_clients"
    ).disabled
    assert entity_registry.async_get(
        f"{SENSOR_DOMAIN}.{device_name}_connected_plc_devices"
    ).disabled
    assert entity_registry.async_get(
        f"{SENSOR_DOMAIN}.{device_name}_neighboring_wi_fi_networks"
    ).disabled
    assert not entity_registry.async_get(
        f"{SENSOR_DOMAIN}.{device_name}_plc_downlink_phy_rate_{PLCNET.devices[1].user_device_name}"
    ).disabled
    assert not entity_registry.async_get(
        f"{SENSOR_DOMAIN}.{device_name}_plc_uplink_phy_rate_{PLCNET.devices[1].user_device_name}"
    ).disabled
    assert entity_registry.async_get(
        f"{SENSOR_DOMAIN}.{device_name}_plc_downlink_phy_rate_{PLCNET.devices[2].user_device_name}"
    ).disabled
    assert entity_registry.async_get(
        f"{SENSOR_DOMAIN}.{device_name}_plc_uplink_phy_rate_{PLCNET.devices[2].user_device_name}"
    ).disabled
    assert entity_registry.async_get(
        f"{SENSOR_DOMAIN}.{device_name}_last_restart_of_the_device"
    ).disabled