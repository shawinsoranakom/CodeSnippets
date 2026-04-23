async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Load a config entry.

    Validate and save sessions per aws credential.
    """
    data = hass.data[DATA_AWS]
    conf = data.config

    if entry.source == config_entries.SOURCE_IMPORT:
        if conf is None:
            # user removed config from configuration.yaml, abort setup
            hass.async_create_task(hass.config_entries.async_remove(entry.entry_id))
            return False

        if conf != entry.data:
            # user changed config from configuration.yaml, use conf to setup
            hass.config_entries.async_update_entry(entry, data=conf)

    if conf is None:
        conf = CONFIG_SCHEMA({DOMAIN: entry.data})[DOMAIN]

    # validate credentials and create sessions
    validation = True
    tasks = [_validate_aws_credentials(hass, cred) for cred in conf[ATTR_CREDENTIALS]]
    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for index, result in enumerate(results):
            name = conf[ATTR_CREDENTIALS][index][CONF_NAME]
            if isinstance(result, Exception):
                _LOGGER.error(
                    "Validating credential [%s] failed: %s",
                    name,
                    result,
                    exc_info=result,
                )
                validation = False
            else:
                data.sessions[name] = result

    # set up notify platform, no entry support for notify component yet,
    # have to use discovery to load platform.
    for notify_config in conf[CONF_NOTIFY]:
        hass.async_create_task(
            discovery.async_load_platform(
                hass, Platform.NOTIFY, DOMAIN, notify_config, data.hass_config
            )
        )

    return validation