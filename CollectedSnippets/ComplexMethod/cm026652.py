def _async_config_entries_for_ids(
    hass: HomeAssistant, entity_ids: list[str] | None, device_ids: list[str] | None
) -> set[str]:
    """Find the config entry ids for a set of entities or devices."""
    config_entry_ids: set[str] = set()
    if entity_ids:
        eng_reg = er.async_get(hass)
        for entity_id in entity_ids:
            if (entry := eng_reg.async_get(entity_id)) and entry.config_entry_id:
                config_entry_ids.add(entry.config_entry_id)
    if device_ids:
        dev_reg = dr.async_get(hass)
        for device_id in device_ids:
            if (device := dev_reg.async_get(device_id)) and device.config_entries:
                config_entry_ids |= device.config_entries
    return config_entry_ids