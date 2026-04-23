def async_update_entry_from_discovery(
    hass: HomeAssistant,
    entry: config_entries.ConfigEntry,
    device: Device30303,
) -> bool:
    """Update a config entry from a discovery."""
    data_updates: dict[str, Any] = {}
    updates: dict[str, Any] = {}
    if not entry.unique_id:
        updates["unique_id"] = dr.format_mac(device.mac)
    if not entry.data.get(CONF_NAME) or is_ip_address(entry.data[CONF_NAME]):
        updates["title"] = data_updates[CONF_NAME] = device.name
    if not entry.data.get(CONF_MODEL) and "-" in device.hostname:
        data_updates[CONF_MODEL] = device.hostname.split("-", maxsplit=1)[0]
    if data_updates:
        updates["data"] = {**entry.data, **data_updates}
    if updates:
        return hass.config_entries.async_update_entry(entry, **updates)
    return False