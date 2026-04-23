async def async_migrate_entry(
    hass: HomeAssistant, entry: SystemMonitorConfigEntry
) -> bool:
    """Migrate old entry."""

    if entry.version > 1:
        # This means the user has downgraded from a future version
        return False

    if entry.version == 1 and entry.minor_version < 3:
        new_options = {**entry.options}
        if entry.minor_version == 1:
            # Migration copies process sensors to binary sensors
            # Repair will remove sensors when user submit the fix
            if processes := entry.options.get(SENSOR_DOMAIN):
                new_options[BINARY_SENSOR_DOMAIN] = processes
        hass.config_entries.async_update_entry(
            entry, options=new_options, version=1, minor_version=2
        )

        if entry.minor_version == 2:
            new_options = {**entry.options}
            if SENSOR_DOMAIN in new_options:
                new_options.pop(SENSOR_DOMAIN)
            hass.config_entries.async_update_entry(
                entry, options=new_options, version=1, minor_version=3
            )

    _LOGGER.debug(
        "Migration to version %s.%s successful", entry.version, entry.minor_version
    )

    return True