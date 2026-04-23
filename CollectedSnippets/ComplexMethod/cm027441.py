async def async_sync_time(service_call: ServiceCall) -> None:
    """Synchronize BSB-LAN device time with Home Assistant."""
    device_id: str = service_call.data[ATTR_DEVICE_ID]

    # Get the device and config entry
    device_registry = dr.async_get(service_call.hass)
    device_entry = device_registry.async_get(device_id)

    if device_entry is None:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="invalid_device_id",
            translation_placeholders={"device_id": device_id},
        )

    # Find the config entry for this device
    matching_entries: list[BSBLanConfigEntry] = [
        entry
        for entry in service_call.hass.config_entries.async_entries(DOMAIN)
        if entry.entry_id in device_entry.config_entries
    ]

    if not matching_entries:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="no_config_entry_for_device",
            translation_placeholders={"device_id": device_entry.name or device_id},
        )

    entry = matching_entries[0]

    # Verify the config entry is loaded
    if entry.state is not ConfigEntryState.LOADED:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="config_entry_not_loaded",
            translation_placeholders={"device_name": device_entry.name or device_id},
        )

    client = entry.runtime_data.client
    await async_sync_device_time(client, device_entry.name or device_id)