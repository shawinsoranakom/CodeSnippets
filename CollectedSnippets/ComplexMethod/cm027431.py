async def _collect_coordinators(
    call: ServiceCall,
) -> list[FullyKioskDataUpdateCoordinator]:
    device_ids: list[str] = call.data[ATTR_DEVICE_ID]
    config_entries = list[ConfigEntry]()
    registry = dr.async_get(call.hass)
    for target in device_ids:
        device = registry.async_get(target)
        if device:
            device_entries = list[ConfigEntry]()
            for entry_id in device.config_entries:
                entry = call.hass.config_entries.async_get_entry(entry_id)
                if entry and entry.domain == DOMAIN:
                    device_entries.append(entry)
            if not device_entries:
                raise HomeAssistantError(f"Device '{target}' is not a {DOMAIN} device")
            config_entries.extend(device_entries)
        else:
            raise HomeAssistantError(f"Device '{target}' not found in device registry")
    coordinators = list[FullyKioskDataUpdateCoordinator]()
    for config_entry in config_entries:
        if config_entry.state != ConfigEntryState.LOADED:
            raise HomeAssistantError(f"{config_entry.title} is not loaded")
        coordinators.append(config_entry.runtime_data)
    return coordinators