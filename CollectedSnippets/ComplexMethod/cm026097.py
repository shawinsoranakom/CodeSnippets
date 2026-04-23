async def _async_create_bridge_with_updated_data(
    hass: HomeAssistant, entry: SamsungTVConfigEntry
) -> SamsungTVBridge:
    """Create a bridge object and update any missing data in the config entry."""
    updated_data: dict[str, str] = {}
    host: str = entry.data[CONF_HOST]
    method: str = entry.data[CONF_METHOD]
    info: dict[str, Any] | None = None

    bridge = _async_get_device_bridge(hass, entry.data)

    mac: str | None = entry.data.get(CONF_MAC)
    model: str | None = entry.data.get(CONF_MODEL)
    # Incorrect MAC cleanup introduced in #110599, can be removed in 2026.3
    mac_is_incorrectly_formatted = mac and dr.format_mac(mac) != mac
    if not mac or not model or mac_is_incorrectly_formatted:
        info = await bridge.async_device_info()

    if not mac or mac_is_incorrectly_formatted:
        LOGGER.debug("Attempting to get mac for %s", host)
        if info:
            mac = mac_from_device_info(info)

        if not mac:
            mac = await hass.async_add_executor_job(
                partial(getmac.get_mac_address, ip=host)
            )

        if mac and mac != "none":
            # Samsung sometimes returns a value of "none" for the mac address
            # this should be ignored
            LOGGER.debug("Updated mac to %s for %s", mac, host)
            updated_data[CONF_MAC] = dr.format_mac(mac)
        else:
            LOGGER.warning("Failed to get mac for %s", host)

    if not model:
        LOGGER.debug("Attempting to get model for %s", host)
        if info:
            model = info.get("device", {}).get("modelName")
            if model:
                LOGGER.debug("Updated model to %s for %s", model, host)
                updated_data[CONF_MODEL] = model

    if model_requires_encryption(model) and method != METHOD_ENCRYPTED_WEBSOCKET:
        LOGGER.debug(
            (
                "Detected model %s for %s. Some televisions from H and J series use "
                "an encrypted protocol but you are using %s which may not be supported"
            ),
            model,
            host,
            method,
        )

    if updated_data:
        data = {**entry.data, **updated_data}
        hass.config_entries.async_update_entry(entry, data=data)

    return bridge