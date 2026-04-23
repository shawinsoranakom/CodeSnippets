async def async_setup_entry(hass: HomeAssistant, entry: AqualinkConfigEntry) -> bool:
    """Set up Aqualink from a config entry."""
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]

    aqualink = AqualinkClient(
        username,
        password,
        httpx_client=get_async_client(hass, alpn_protocols=SSL_ALPN_HTTP11_HTTP2),
    )
    try:
        await aqualink.login()
    except AqualinkServiceUnauthorizedException as auth_exception:
        await aqualink.close()
        raise ConfigEntryAuthFailed(
            "Invalid credentials for iAquaLink"
        ) from auth_exception
    except (AqualinkServiceException, TimeoutError, httpx.HTTPError) as aio_exception:
        await aqualink.close()
        raise ConfigEntryNotReady(
            f"Error while attempting login: {aio_exception}"
        ) from aio_exception

    try:
        systems = await aqualink.get_systems()
    except AqualinkServiceUnauthorizedException as auth_exception:
        await aqualink.close()
        raise ConfigEntryAuthFailed(
            "Invalid credentials for iAquaLink"
        ) from auth_exception
    except AqualinkServiceException as svc_exception:
        await aqualink.close()
        raise ConfigEntryNotReady(
            f"Error while attempting to retrieve systems list: {svc_exception}"
        ) from svc_exception

    systems_list = list(systems.values())
    if not systems_list:
        await aqualink.close()
        raise ConfigEntryError("No systems detected or supported")

    runtime_data = AqualinkRuntimeData(
        aqualink,
        coordinators={},
        binary_sensors=[],
        lights=[],
        sensors=[],
        switches=[],
        thermostats=[],
    )
    for system in systems_list:
        coordinator = AqualinkDataUpdateCoordinator(hass, entry, system)
        runtime_data.coordinators[system.serial] = coordinator
        try:
            await coordinator.async_config_entry_first_refresh()
        except ConfigEntryAuthFailed:
            await aqualink.close()
            raise

        try:
            devices = await system.get_devices()
        except AqualinkServiceUnauthorizedException as auth_exception:
            await aqualink.close()
            raise ConfigEntryAuthFailed(
                "Invalid credentials for iAquaLink"
            ) from auth_exception
        except AqualinkServiceException as svc_exception:
            await aqualink.close()
            raise ConfigEntryNotReady(
                f"Error while attempting to retrieve devices list: {svc_exception}"
            ) from svc_exception

        device_registry = dr.async_get(hass)
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            name=system.name,
            identifiers={(DOMAIN, system.serial)},
            manufacturer="Jandy",
            serial_number=system.serial,
        )

        for dev in devices.values():
            if isinstance(dev, AqualinkThermostat):
                runtime_data.thermostats += [dev]
            elif isinstance(dev, AqualinkLight):
                runtime_data.lights += [dev]
            elif isinstance(dev, AqualinkSwitch):
                runtime_data.switches += [dev]
            elif isinstance(dev, AqualinkBinarySensor):
                runtime_data.binary_sensors += [dev]
            elif isinstance(dev, AqualinkSensor):
                runtime_data.sensors += [dev]

    _LOGGER.debug(
        "Got %s binary sensors: %s",
        len(runtime_data.binary_sensors),
        runtime_data.binary_sensors,
    )
    _LOGGER.debug("Got %s lights: %s", len(runtime_data.lights), runtime_data.lights)
    _LOGGER.debug("Got %s sensors: %s", len(runtime_data.sensors), runtime_data.sensors)
    _LOGGER.debug(
        "Got %s switches: %s", len(runtime_data.switches), runtime_data.switches
    )
    _LOGGER.debug(
        "Got %s thermostats: %s",
        len(runtime_data.thermostats),
        runtime_data.thermostats,
    )

    entry.runtime_data = runtime_data

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True