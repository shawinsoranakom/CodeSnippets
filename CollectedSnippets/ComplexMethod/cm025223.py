async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Check connectivity and version of KEBA charging station."""
    host = config[DOMAIN][CONF_HOST]
    rfid = config[DOMAIN][CONF_RFID]
    refresh_interval = config[DOMAIN][CONF_FS_INTERVAL]
    keba = KebaHandler(hass, host, rfid, refresh_interval)
    hass.data[DOMAIN] = keba

    # Wait for KebaHandler setup complete (initial values loaded)
    if not await keba.setup():
        _LOGGER.error("Could not find a charging station at %s", host)
        return False

    # Set failsafe mode at start up of Home Assistant
    failsafe = config[DOMAIN][CONF_FS]
    timeout = config[DOMAIN][CONF_FS_TIMEOUT] if failsafe else 0
    fallback = config[DOMAIN][CONF_FS_FALLBACK] if failsafe else 0
    persist = config[DOMAIN][CONF_FS_PERSIST] if failsafe else 0
    try:
        hass.loop.create_task(keba.set_failsafe(timeout, fallback, persist))
    except ValueError as ex:
        _LOGGER.warning("Could not set failsafe mode %s", ex)

    # Register services to hass
    async def execute_service(call: ServiceCall) -> None:
        """Execute a service to KEBA charging station.

        This must be a member function as we need access to the keba
        object here.
        """
        function_name = _SERVICE_MAP[call.service]
        function_call = getattr(keba, function_name)
        await function_call(call.data)

    for service in _SERVICE_MAP:
        hass.services.async_register(DOMAIN, service, execute_service)

    # Load components
    for platform in PLATFORMS:
        hass.async_create_task(
            discovery.async_load_platform(hass, platform, DOMAIN, {}, config)
        )

    # Start periodic polling of charging station data
    keba.start_periodic_request()

    return True