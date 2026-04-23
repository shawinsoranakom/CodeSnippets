def _async_get_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry, device: DeviceEntry | None = None
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    hkid = entry.data["AccessoryPairingID"]
    connection: HKDevice = hass.data[KNOWN_DEVICES][hkid]

    data: dict[str, Any] = {
        "config-entry": {
            "title": entry.title,
            "version": entry.version,
            "data": async_redact_data(entry.data, REDACTED_CONFIG_ENTRY_KEYS),
        }
    }

    # This is the raw data as returned by homekit
    # It is roughly equivalent to what is in .storage/homekit_controller-entity-map
    # But it also has the latest values seen by the polling or events
    data["entity-map"] = accessories = connection.entity_map.serialize()
    data["config-num"] = connection.config_num

    # It contains serial numbers, which we should strip out
    for accessory in accessories:
        for service in accessory.get("services", []):
            for char in service.get("characteristics", []):
                if char["type"] in REDACTED_CHARACTERISTICS:
                    char["value"] = REDACTED

    if device:
        data["device"] = _async_get_diagnostics_for_device(hass, device)
    else:
        device_registry = dr.async_get(hass)

        devices = data["devices"] = []
        for device_id in connection.devices.values():
            if not (device := device_registry.async_get(device_id)):
                continue
            devices.append(_async_get_diagnostics_for_device(hass, device))

    return data