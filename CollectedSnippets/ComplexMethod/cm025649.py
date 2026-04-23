async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: NetatmoConfigEntry, device_entry: DeviceEntry
) -> bool:
    """Remove a config entry from a device."""
    data = config_entry.runtime_data
    modules = [m for h in data.account.homes.values() for m in h.modules]
    rooms = [r for h in data.account.homes.values() for r in h.rooms]

    return not any(
        identifier
        for identifier in device_entry.identifiers
        if (identifier[0] == DOMAIN and identifier[1] in modules)
        or identifier[1] in rooms
    )