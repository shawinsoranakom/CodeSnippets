async def _get_client_and_ha_id(
    hass: HomeAssistant, device_id: str
) -> tuple[HomeConnectClient, str]:
    device_registry = dr.async_get(hass)
    device_entry = device_registry.async_get(device_id)
    if device_entry is None:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="device_entry_not_found",
            translation_placeholders={
                "device_id": device_id,
            },
        )
    entry: HomeConnectConfigEntry | None = None
    for entry_id in device_entry.config_entries:
        _entry = hass.config_entries.async_get_entry(entry_id)
        assert _entry
        if _entry.domain == DOMAIN:
            entry = cast(HomeConnectConfigEntry, _entry)
            break
    if entry is None:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="config_entry_not_found",
            translation_placeholders={
                "device_id": device_id,
            },
        )

    ha_id = next(
        (
            identifier[1]
            for identifier in device_entry.identifiers
            if identifier[0] == DOMAIN
        ),
        None,
    )
    if ha_id is None:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="appliance_not_found",
            translation_placeholders={
                "device_id": device_id,
            },
        )
    return entry.runtime_data.client, ha_id