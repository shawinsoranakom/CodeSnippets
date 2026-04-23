def remove_stale_devices(
    hass: HomeAssistant, config_entry: ConfigEntry, devices: list[Device]
) -> None:
    """Remove stale devices from device registry."""
    device_registry = dr.async_get(hass)
    device_entries = dr.async_entries_for_config_entry(
        device_registry, config_entry.entry_id
    )
    all_device_ids = {str(device.id) for device in devices}

    for device_entry in device_entries:
        device_id: str | None = None
        gateway_id: str | None = None

        for identifier in device_entry.identifiers:
            if identifier[0] != DOMAIN:
                continue

            _id = identifier[1]

            # Identify gateway device.
            if _id == config_entry.data[CONF_GATEWAY_ID]:
                gateway_id = _id
                break

            device_id = _id.replace(f"{config_entry.data[CONF_GATEWAY_ID]}-", "")
            break

        if gateway_id is not None:
            # Do not remove gateway device entry.
            continue

        if device_id is None or device_id not in all_device_ids:
            # If device_id is None an invalid device entry was found for this config entry.
            # If the device_id is not in existing device ids it's a stale device entry.
            # Remove config entry from this device entry in either case.
            device_registry.async_update_device(
                device_entry.id, remove_config_entry_id=config_entry.entry_id
            )