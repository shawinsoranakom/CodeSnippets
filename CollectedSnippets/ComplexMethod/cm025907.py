async def _async_fix_unique_id(
    hass: HomeAssistant, controller: AsyncRainbirdController, entry: RainbirdConfigEntry
) -> bool:
    """Update the config entry with a unique id based on the mac address."""
    _LOGGER.debug("Checking for migration of config entry (%s)", entry.unique_id)
    if not (mac_address := entry.data.get(CONF_MAC)):
        try:
            wifi_params = await controller.get_wifi_params()
        except RainbirdApiException as err:
            _LOGGER.warning("Unable to fix missing unique id: %s", err)
            return True

        if (mac_address := wifi_params.mac_address) is None:
            _LOGGER.warning("Unable to fix missing unique id (mac address was None)")
            return True

    new_unique_id = format_mac(mac_address)
    if entry.unique_id == new_unique_id and CONF_MAC in entry.data:
        _LOGGER.debug("Config entry already in correct state")
        return True

    entries = hass.config_entries.async_entries(DOMAIN)
    for existing_entry in entries:
        if existing_entry.unique_id == new_unique_id:
            _LOGGER.warning(
                "Unable to fix missing unique id (already exists); Removing duplicate entry"
            )
            hass.async_create_background_task(
                hass.config_entries.async_remove(entry.entry_id),
                "Remove rainbird config entry",
            )
            return False

    _LOGGER.debug("Updating unique id to %s", new_unique_id)
    hass.config_entries.async_update_entry(
        entry,
        unique_id=new_unique_id,
        data={
            **entry.data,
            CONF_MAC: mac_address,
        },
    )
    return True