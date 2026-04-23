async def async_setup_entry(hass: HomeAssistant, entry: TractiveConfigEntry) -> bool:
    """Set up tractive from a config entry."""
    data = entry.data

    client = aiotractive.Tractive(
        data[CONF_EMAIL],
        data[CONF_PASSWORD],
        session=async_get_clientsession(hass),
        client_id=CLIENT_ID,
    )
    try:
        creds = await client.authenticate()
    except aiotractive.exceptions.UnauthorizedError as error:
        await client.close()
        raise ConfigEntryAuthFailed from error
    except aiotractive.exceptions.TractiveError as error:
        await client.close()
        raise ConfigEntryNotReady from error

    if TYPE_CHECKING:
        assert creds is not None

    tractive = TractiveClient(hass, client, creds["user_id"], entry)

    try:
        trackable_objects = await client.trackable_objects()
        trackables = await asyncio.gather(
            *(_generate_trackables(client, item) for item in trackable_objects)
        )
    except aiotractive.exceptions.TractiveError as error:
        raise ConfigEntryNotReady from error

    # When the pet defined in Tractive has no tracker linked we get None as `trackable`.
    # So we have to remove None values from trackables list.
    filtered_trackables = [item for item in trackables if item]

    entry.runtime_data = TractiveData(tractive, filtered_trackables)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Send initial health overview data to sensors after platforms are set up
    for item in filtered_trackables:
        if item.health_overview:
            tractive.send_health_overview_update(item.health_overview)

    async def cancel_listen_task(_: Event) -> None:
        await tractive.unsubscribe()

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, cancel_listen_task)
    )
    entry.async_on_unload(tractive.unsubscribe)

    # Remove sensor entities that are no longer supported by the Tractive API
    entity_reg = er.async_get(hass)
    for item in filtered_trackables:
        for key in ("activity_label", "calories", "sleep_label"):
            if entity_id := entity_reg.async_get_entity_id(
                SENSOR_DOMAIN, DOMAIN, f"{item.trackable['_id']}_{key}"
            ):
                entity_reg.async_remove(entity_id)

    return True