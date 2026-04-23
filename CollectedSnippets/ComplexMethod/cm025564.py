async def async_setup_entry(hass: HomeAssistant, entry: HomeConnectConfigEntry) -> bool:
    """Set up Home Connect from a config entry."""
    try:
        implementation = await async_get_config_entry_implementation(hass, entry)
    except ImplementationUnavailableError as err:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="oauth2_implementation_unavailable",
        ) from err

    session = OAuth2Session(hass, entry, implementation)

    config_entry_auth = AsyncConfigEntryAuth(hass, session)
    try:
        await config_entry_auth.async_get_access_token()
    except aiohttp.ClientResponseError as err:
        if 400 <= err.status < 500:
            raise ConfigEntryAuthFailed from err
        raise ConfigEntryNotReady from err
    except aiohttp.ClientError as err:
        raise ConfigEntryNotReady from err

    home_connect_client = HomeConnectClient(config_entry_auth)

    runtime_data = HomeConnectRuntimeData(hass, entry, home_connect_client)
    await runtime_data.setup_appliance_coordinators()
    entry.runtime_data = runtime_data

    appliances_identifiers = {
        (entry.domain, ha_id) for ha_id in entry.runtime_data.appliance_coordinators
    }
    device_registry = dr.async_get(hass)
    device_entries = dr.async_entries_for_config_entry(
        device_registry, config_entry_id=entry.entry_id
    )

    for device in device_entries:
        if not device.identifiers.intersection(appliances_identifiers):
            device_registry.async_update_device(
                device.id, remove_config_entry_id=entry.entry_id
            )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    for listener, context in runtime_data.global_listeners.values():
        # We call the PAIRED event listener to start adding entities
        # from the appliances we already found above
        assert isinstance(context, tuple)
        if EventKey.BSH_COMMON_APPLIANCE_PAIRED in context:
            listener()

    entry.runtime_data.start_event_listener()

    for (
        appliance_id,
        appliance_coordinator,
    ) in entry.runtime_data.appliance_coordinators.items():
        # We refresh each appliance coordinator in the background.
        # to ensure that setup time is not impacted by this refresh.
        entry.async_create_background_task(
            hass,
            appliance_coordinator.async_refresh(),
            f"home_connect-initial-full-refresh-{entry.entry_id}-{appliance_id}",
        )

    return True