def _remove_missing_devices(
    hass: HomeAssistant,
    entry: DaliCenterConfigEntry,
    devices: Sequence[Device],
    gateway_identifier: tuple[str, str],
) -> None:
    """Detach devices that are no longer provided by the gateway."""
    device_registry = dr.async_get(hass)
    known_device_ids = {device.dev_id for device in devices}

    for device_entry in dr.async_entries_for_config_entry(
        device_registry, entry.entry_id
    ):
        if gateway_identifier in device_entry.identifiers:
            continue

        domain_device_ids = {
            identifier[1]
            for identifier in device_entry.identifiers
            if identifier[0] == DOMAIN
        }

        if not domain_device_ids:
            continue

        if domain_device_ids.isdisjoint(known_device_ids):
            device_registry.async_update_device(
                device_entry.id,
                remove_config_entry_id=entry.entry_id,
            )