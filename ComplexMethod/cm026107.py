async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate an old config entry."""

    if config_entry.version == 1:
        _LOGGER.debug(
            "Migrating from version %s.%s",
            config_entry.version,
            config_entry.minor_version,
        )
        options = dict(config_entry.options)
        if (incl_filters := options.pop(CONF_INCL_FILTER, None)) not in {None, ""}:
            options[CONF_INCL_FILTER] = [incl_filters]
        else:
            options[CONF_INCL_FILTER] = DEFAULT_FILTER
        if (excl_filters := options.pop(CONF_EXCL_FILTER, None)) not in {None, ""}:
            options[CONF_EXCL_FILTER] = [excl_filters]
        else:
            options[CONF_EXCL_FILTER] = DEFAULT_FILTER
        hass.config_entries.async_update_entry(config_entry, options=options, version=2)
        _LOGGER.debug(
            "Migration to version %s.%s successful",
            config_entry.version,
            config_entry.minor_version,
        )

    if config_entry.version == 2 and config_entry.minor_version == 1:
        _LOGGER.debug(
            "Migrating from version %s.%s",
            config_entry.version,
            config_entry.minor_version,
        )
        options = dict(config_entry.options)
        options[CONF_TIME_DELTA] = DEFAULT_TIME_DELTA
        hass.config_entries.async_update_entry(
            config_entry, options=options, minor_version=2
        )
        _LOGGER.debug(
            "Migration to version %s.%s successful",
            config_entry.version,
            config_entry.minor_version,
        )

    if config_entry.version == 2 and config_entry.minor_version == 2:
        _LOGGER.debug(
            "Migrating from version %s.%s",
            config_entry.version,
            config_entry.minor_version,
        )
        options = dict(config_entry.options)
        options.setdefault(
            CONF_BASE_COORDINATES,
            default_base_coordinates_for_region(config_entry.data[CONF_REGION]),
        )
        hass.config_entries.async_update_entry(
            config_entry, options=options, minor_version=3
        )
        _LOGGER.debug(
            "Migration to version %s.%s successful",
            config_entry.version,
            config_entry.minor_version,
        )

    return True