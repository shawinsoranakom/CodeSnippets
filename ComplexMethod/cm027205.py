def _async_get_target(
    hass: HomeAssistant, call: ServiceCall
) -> tuple[UnifiAccessConfigEntry, str]:
    """Resolve a service call to a UniFi Access config entry and door ID."""
    device_registry = dr.async_get(hass)
    device_id = call.data[ATTR_DEVICE_ID]
    if (device := device_registry.async_get(device_id)) is None:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="invalid_target",
        )

    for entry_id in device.config_entries:
        if (
            entry := hass.config_entries.async_get_entry(entry_id)
        ) is None or entry.domain != DOMAIN:
            continue

        config_entry: UnifiAccessConfigEntry = service.async_get_config_entry(
            hass, DOMAIN, entry_id
        )
        coordinator = config_entry.runtime_data
        for identifier_domain, identifier_value in device.identifiers:
            if (
                identifier_domain == DOMAIN
                and identifier_value in coordinator.data.doors
            ):
                return config_entry, identifier_value

    raise ServiceValidationError(
        translation_domain=DOMAIN,
        translation_key="invalid_target",
    )