def _async_get_switchbot_entry_for_device_id(
    hass: HomeAssistant, device_id: str
) -> SwitchbotConfigEntry:
    """Return the loaded SwitchBot config entry for a device id."""
    device_registry = dr.async_get(hass)
    if not (device_entry := device_registry.async_get(device_id)):
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="invalid_device_id",
            translation_placeholders={"device_id": device_id},
        )

    entries = [
        hass.config_entries.async_get_entry(entry_id)
        for entry_id in device_entry.config_entries
    ]
    switchbot_entries = [
        entry for entry in entries if entry is not None and entry.domain == DOMAIN
    ]
    if not switchbot_entries:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="device_not_belonging",
            translation_placeholders={"device_id": device_id},
        )

    if not (
        loaded_entry := next(
            (
                entry
                for entry in switchbot_entries
                if entry.state is ConfigEntryState.LOADED
            ),
            None,
        )
    ):
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="device_entry_not_loaded",
            translation_placeholders={"device_id": device_id},
        )

    return loaded_entry