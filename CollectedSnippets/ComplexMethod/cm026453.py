async def async_migrate_entry(hass: HomeAssistant, entry: NinaConfigEntry) -> bool:
    """Migrate the config to the new format."""

    version = entry.version
    minor_version = entry.minor_version

    _LOGGER.debug("Migrating from version %s.%s", version, minor_version)
    if entry.version > 1:
        # This means the user has downgraded from a future version
        return False

    new_data: dict[str, Any] = {**entry.data, CONF_FILTERS: {}}

    if version == 1 and minor_version == 1:
        if CONF_HEADLINE_FILTER not in entry.data:
            filter_regex = NO_MATCH_REGEX

            if entry.data.get(CONF_FILTER_CORONA, None):
                filter_regex = ".*corona.*"

            new_data[CONF_HEADLINE_FILTER] = filter_regex
            new_data.pop(CONF_FILTER_CORONA, None)

        if CONF_AREA_FILTER not in entry.data:
            new_data[CONF_AREA_FILTER] = ALL_MATCH_REGEX

        hass.config_entries.async_update_entry(
            entry,
            data=new_data,
            minor_version=2,
        )
        minor_version = 2

    if version == 1 and minor_version == 2:
        new_data[CONF_FILTERS][CONF_HEADLINE_FILTER] = entry.data[CONF_HEADLINE_FILTER]
        new_data.pop(CONF_HEADLINE_FILTER, None)

        new_data[CONF_FILTERS][CONF_AREA_FILTER] = entry.data[CONF_AREA_FILTER]
        new_data.pop(CONF_AREA_FILTER, None)

        hass.config_entries.async_update_entry(
            entry,
            data=new_data,
            minor_version=3,
        )

    return True