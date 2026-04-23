async def async_setup_entry(
    hass: HomeAssistant, config_entry: GrowattConfigEntry
) -> bool:
    """Set up Growatt from a config entry."""

    config = config_entry.data
    url = config.get(CONF_URL, DEFAULT_URL)

    # If the URL has been deprecated then change to the default instead
    if url in DEPRECATED_URLS:
        url = DEFAULT_URL
        new_data = dict(config_entry.data)
        new_data[CONF_URL] = url
        hass.config_entries.async_update_entry(config_entry, data=new_data)

    # Determine API version and get devices
    # Note: auth_type field is guaranteed to exist after migration
    if config.get(CONF_AUTH_TYPE) == AUTH_API_TOKEN:
        # V1 API (token-based, no login needed)
        token = config[CONF_TOKEN]
        api = growattServer.OpenApiV1(token=token)
        api.server_url = url
        devices, plant_id = await hass.async_add_executor_job(
            get_device_list_v1, api, config
        )
    elif config.get(CONF_AUTH_TYPE) == AUTH_PASSWORD:
        # Classic API (username/password with login)
        username = config[CONF_USERNAME]
        password = config[CONF_PASSWORD]

        # Check if migration cached an authenticated API instance for us to reuse.
        # This avoids calling login() twice (once in migration, once here) which
        # would trigger rate limiting.
        cached_api = hass.data.get(DOMAIN, {}).pop(
            f"{CACHED_API_KEY}{config_entry.entry_id}", None
        )

        if cached_api:
            # Reuse the logged-in API instance from migration (rate limit optimization)
            api = cached_api
            _LOGGER.debug("Reusing logged-in session from migration")
        else:
            # No cached API (normal setup or migration didn't run)
            # Create new API instance and login
            api, _ = await _create_api_and_login(hass, username, password, url)

        # Get plant_id and devices using the authenticated session
        plant_id = config[CONF_PLANT_ID]
        try:
            devices = await hass.async_add_executor_job(api.device_list, plant_id)
        except (RequestException, JSONDecodeError) as ex:
            raise ConfigEntryError(
                f"Error communicating with Growatt API during device list: {ex}"
            ) from ex
    else:
        raise ConfigEntryError("Unknown authentication type in config entry.")

    # Create a coordinator for the total sensors
    total_coordinator = GrowattCoordinator(
        hass, config_entry, plant_id, "total", plant_id
    )

    # Create coordinators for each device
    device_coordinators = {
        device["deviceSn"]: GrowattCoordinator(
            hass, config_entry, device["deviceSn"], device["deviceType"], plant_id
        )
        for device in devices
        if device["deviceType"] in ["inverter", "tlx", "storage", "mix", "min", "sph"]
    }

    # Perform the first refresh for the total coordinator
    await total_coordinator.async_config_entry_first_refresh()

    # Perform the first refresh for each device coordinator
    for device_coordinator in device_coordinators.values():
        await device_coordinator.async_config_entry_first_refresh()

    # Store runtime data in the config entry
    config_entry.runtime_data = GrowattRuntimeData(
        total_coordinator=total_coordinator,
        devices=device_coordinators,
    )

    # Set up all the entities
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True