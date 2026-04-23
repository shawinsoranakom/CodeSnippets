def async_update_entry_from_discovery(
    hass: HomeAssistant,
    entry: FluxLedConfigEntry,
    device: FluxLEDDiscovery,
    model_num: int | None,
    allow_update_mac: bool,
) -> bool:
    """Update a config entry from a flux_led discovery."""
    data_updates: dict[str, Any] = {}
    mac_address = device[ATTR_ID]
    assert mac_address is not None
    updates: dict[str, Any] = {}
    formatted_mac = dr.format_mac(mac_address)
    if not entry.unique_id or (
        allow_update_mac
        and entry.unique_id != formatted_mac
        and mac_matches_by_one(formatted_mac, entry.unique_id)
    ):
        updates["unique_id"] = formatted_mac
    if model_num and entry.data.get(CONF_MODEL_NUM) != model_num:
        data_updates[CONF_MODEL_NUM] = model_num
    async_populate_data_from_discovery(entry.data, data_updates, device)
    if is_ip_address(entry.title):
        updates["title"] = async_name_from_discovery(device, model_num)
    title_matches_name = entry.title == entry.data.get(CONF_NAME)
    if data_updates or title_matches_name:
        updates["data"] = {**entry.data, **data_updates}
        if title_matches_name:
            del updates["data"][CONF_NAME]
    # If the title has changed and the config entry is loaded, a listener is
    # in place, and we should not reload
    if updates and not ("title" in updates and entry.state is ConfigEntryState.LOADED):
        return hass.config_entries.async_update_entry(entry, **updates)
    return False