async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: EnphaseConfigEntry, device_entry: dr.DeviceEntry
) -> bool:
    """Remove an enphase_envoy config entry from a device."""
    dev_ids = {dev_id[1] for dev_id in device_entry.identifiers if dev_id[0] == DOMAIN}
    coordinator = config_entry.runtime_data
    envoy_data = coordinator.envoy.data
    envoy_serial_num = config_entry.unique_id
    if envoy_serial_num in dev_ids:
        return False
    if envoy_data:
        if envoy_data.inverters:
            for inverter in envoy_data.inverters:
                if str(inverter) in dev_ids:
                    return False
        if envoy_data.encharge_inventory:
            for encharge in envoy_data.encharge_inventory:
                if str(encharge) in dev_ids:
                    return False
        if envoy_data.enpower:
            if str(envoy_data.enpower.serial_number) in dev_ids:
                return False
    return True