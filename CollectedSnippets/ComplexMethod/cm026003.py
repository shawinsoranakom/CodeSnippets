async def async_migrate_entry(
    hass: HomeAssistant, entry: OpenRouterConfigEntry
) -> bool:
    """Migrate config entry."""
    LOGGER.debug("Migrating from version %s.%s", entry.version, entry.minor_version)

    if entry.version > 1 or (entry.version == 1 and entry.minor_version > 2):
        return False

    if entry.version == 1 and entry.minor_version < 2:
        for subentry in entry.subentries.values():
            if CONF_WEB_SEARCH in subentry.data:
                continue

            updated_data = {**subentry.data, CONF_WEB_SEARCH: False}

            hass.config_entries.async_update_subentry(
                entry, subentry, data=updated_data
            )

        hass.config_entries.async_update_entry(entry, minor_version=2)

    LOGGER.info(
        "Migration to version %s.%s successful", entry.version, entry.minor_version
    )

    return True