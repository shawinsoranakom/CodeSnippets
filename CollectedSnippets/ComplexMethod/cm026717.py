async def check_migration(hass: core.HomeAssistant, entry: HueConfigEntry) -> None:
    """Check if config entry needs any migration actions."""
    host = entry.data[CONF_HOST]

    # migrate CONF_USERNAME --> CONF_API_KEY
    if CONF_USERNAME in entry.data:
        LOGGER.info("Migrate %s to %s in schema", CONF_USERNAME, CONF_API_KEY)
        data = dict(entry.data)
        data[CONF_API_KEY] = data.pop(CONF_USERNAME)
        hass.config_entries.async_update_entry(entry, data=data)

    if (conf_api_version := entry.data.get(CONF_API_VERSION, 1)) == 1:
        # a bridge might have upgraded firmware since last run so
        # we discover its capabilities at every startup
        websession = aiohttp_client.async_get_clientsession(hass)
        if await is_v2_bridge(host, websession):
            supported_api_version = 2
        else:
            supported_api_version = 1
        LOGGER.debug(
            "Configured api version is %s and supported api version %s for bridge %s",
            conf_api_version,
            supported_api_version,
            host,
        )

        # the call to `is_v2_bridge` returns (silently) False even on connection error
        # so if a migration is needed it will be done on next startup

        if conf_api_version == 1 and supported_api_version == 2:
            # run entity/device schema migration for v2
            await handle_v2_migration(hass, entry)

        # store api version in entry data
        if (
            CONF_API_VERSION not in entry.data
            or conf_api_version != supported_api_version
        ):
            data = dict(entry.data)
            data[CONF_API_VERSION] = supported_api_version
            hass.config_entries.async_update_entry(entry, data=data)