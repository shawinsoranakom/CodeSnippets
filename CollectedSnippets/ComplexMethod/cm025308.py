async def async_setup_entry(hass: HomeAssistant, entry: GeniusHubConfigEntry) -> bool:
    """Create a Genius Hub system."""
    if CONF_TOKEN in entry.data and CONF_MAC in entry.data:
        entity_registry = er.async_get(hass)
        registry_entries = er.async_entries_for_config_entry(
            entity_registry, entry.entry_id
        )
        for reg_entry in registry_entries:
            if reg_entry.unique_id.startswith(entry.data[CONF_MAC]):
                entity_registry.async_update_entity(
                    reg_entry.entity_id,
                    new_unique_id=reg_entry.unique_id.replace(
                        entry.data[CONF_MAC], entry.entry_id
                    ),
                )

    session = async_get_clientsession(hass)
    if CONF_HOST in entry.data:
        client = GeniusHub(
            entry.data[CONF_HOST],
            username=entry.data[CONF_USERNAME],
            password=entry.data[CONF_PASSWORD],
            session=session,
        )
    else:
        client = GeniusHub(entry.data[CONF_TOKEN], session=session)

    unique_id = entry.unique_id or entry.entry_id

    broker = entry.runtime_data = GeniusBroker(hass, client, unique_id)

    try:
        await client.update()
    except aiohttp.ClientResponseError as err:
        _LOGGER.error("Setup failed, check your configuration, %s", err)
        return False
    broker.make_debug_log_entries()

    async_track_time_interval(hass, broker.async_update, SCAN_INTERVAL)

    setup_service_functions(hass, broker)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True