def get_block_coordinator_by_device_id(
    hass: HomeAssistant, device_id: str
) -> ShellyBlockCoordinator | None:
    """Get a Shelly block device coordinator for the given device id."""
    dev_reg = dr.async_get(hass)
    if device := dev_reg.async_get(device_id):
        for config_entry in device.config_entries:
            entry = hass.config_entries.async_get_entry(config_entry)
            if (
                entry
                and entry.state is ConfigEntryState.LOADED
                and hasattr(entry, "runtime_data")
                and isinstance(entry.runtime_data, ShellyEntryData)
                and (coordinator := entry.runtime_data.block)
            ):
                return coordinator

    return None