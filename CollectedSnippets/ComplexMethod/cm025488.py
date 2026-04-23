async def async_setup_entry(hass: HomeAssistant, entry: OverkizDataConfigEntry) -> bool:
    """Set up Overkiz from a config entry."""
    client: OverkizClient | None = None
    api_type = entry.data.get(CONF_API_TYPE, APIType.CLOUD)

    # Local API
    if api_type == APIType.LOCAL:
        client = create_local_client(
            hass,
            host=entry.data[CONF_HOST],
            token=entry.data[CONF_TOKEN],
            verify_ssl=entry.data[CONF_VERIFY_SSL],
        )

    # Overkiz Cloud API
    else:
        client = create_cloud_client(
            hass,
            username=entry.data[CONF_USERNAME],
            password=entry.data[CONF_PASSWORD],
            server=SUPPORTED_SERVERS[entry.data[CONF_HUB]],
        )

    await _async_migrate_entries(hass, entry)

    try:
        await client.login()
        setup = await client.get_setup()

        # Local API does expose scenarios, but they are not functional.
        # Tracked in https://github.com/Somfy-Developer/Somfy-TaHoma-Developer-Mode/issues/21
        if api_type == APIType.CLOUD:
            scenarios = await client.get_scenarios()
        else:
            scenarios = []
    except (
        BadCredentialsException,
        NotSuchTokenException,
        NotAuthenticatedException,
    ) as exception:
        raise ConfigEntryAuthFailed("Invalid authentication") from exception
    except TooManyRequestsException as exception:
        raise ConfigEntryNotReady("Too many requests, try again later") from exception
    except (TimeoutError, ClientError) as exception:
        raise ConfigEntryNotReady("Failed to connect") from exception
    except MaintenanceException as exception:
        raise ConfigEntryNotReady("Server is down for maintenance") from exception

    coordinator = OverkizDataUpdateCoordinator(
        hass,
        entry,
        LOGGER,
        client=client,
        devices=setup.devices,
        places=setup.root_place,
    )

    await coordinator.async_config_entry_first_refresh()

    if coordinator.is_stateless:
        LOGGER.debug(
            "All devices have an assumed state. Update interval has been reduced to: %s",
            UPDATE_INTERVAL_ALL_ASSUMED_STATE,
        )
        coordinator.set_update_interval(UPDATE_INTERVAL_ALL_ASSUMED_STATE)

    if api_type == APIType.LOCAL:
        LOGGER.debug(
            "Devices connect via Local API. Update interval has been reduced to: %s",
            UPDATE_INTERVAL_LOCAL,
        )
        coordinator.set_update_interval(UPDATE_INTERVAL_LOCAL)

    platforms: defaultdict[Platform, list[Device]] = defaultdict(list)

    entry.runtime_data = HomeAssistantOverkizData(
        coordinator=coordinator, platforms=platforms, scenarios=scenarios
    )

    # Map Overkiz entities to Home Assistant platform
    for device in coordinator.data.values():
        LOGGER.debug(
            (
                "The following device has been retrieved. Report an issue if not"
                " supported correctly (%s)"
            ),
            device,
        )

        if platform := OVERKIZ_DEVICE_TO_PLATFORM.get(
            device.widget
        ) or OVERKIZ_DEVICE_TO_PLATFORM.get(device.ui_class):
            platforms[platform].append(device)

    device_registry = dr.async_get(hass)

    for gateway in setup.gateways:
        LOGGER.debug("Added gateway (%s)", gateway)

        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, gateway.id)},
            model=gateway.type.beautify_name if gateway.type else None,
            model_id=str(gateway.type),
            manufacturer=client.server.manufacturer,
            name=gateway.type.beautify_name if gateway.type else gateway.id,
            sw_version=gateway.connectivity.protocol_version,
            hw_version=f"{gateway.type}:{gateway.sub_type}"
            if gateway.type and gateway.sub_type
            else None,
            configuration_url=client.server.configuration_url,
        )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True