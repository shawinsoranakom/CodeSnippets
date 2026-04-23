async def async_setup_entry(hass: HomeAssistant, entry: IsyConfigEntry) -> bool:
    """Set up the ISY 994 integration."""
    isy_config = entry.data
    isy_options = entry.options

    # Required
    user = isy_config[CONF_USERNAME]
    password = isy_config[CONF_PASSWORD]
    host = urlparse(isy_config[CONF_HOST])

    # Optional
    tls_version = isy_config.get(CONF_TLS_VER)
    ignore_identifier = isy_options.get(CONF_IGNORE_STRING, DEFAULT_IGNORE_STRING)
    sensor_identifier = isy_options.get(CONF_SENSOR_STRING, DEFAULT_SENSOR_STRING)

    if host.scheme == SCHEME_HTTP:
        https = False
        port = host.port or 80
        session = aiohttp_client.async_create_clientsession(
            hass, verify_ssl=False, cookie_jar=CookieJar(unsafe=True)
        )
    elif host.scheme == SCHEME_HTTPS:
        https = True
        port = host.port or 443
        session = aiohttp_client.async_get_clientsession(hass)
    else:
        _LOGGER.error("The ISY/IoX host value in configuration is invalid")
        return False

    # Connect to ISY controller.
    isy = ISY(
        host.hostname,
        port,
        username=user,
        password=password,
        use_https=https,
        tls_ver=tls_version,
        webroot=host.path,
        websession=session,
        use_websocket=True,
    )

    try:
        async with asyncio.timeout(60):
            await isy.initialize()
    except TimeoutError as err:
        raise ConfigEntryNotReady(
            "Timed out initializing the ISY; device may be busy, trying again later:"
            f" {err}"
        ) from err
    except ISYInvalidAuthError as err:
        raise ConfigEntryAuthFailed(f"Invalid credentials for the ISY: {err}") from err
    except ISYConnectionError as err:
        raise ConfigEntryNotReady(
            f"Failed to connect to the ISY, please adjust settings and try again: {err}"
        ) from err
    except ISYResponseParseError as err:
        raise ConfigEntryNotReady(
            "Invalid XML response from ISY; Ensure the ISY is running the latest"
            f" firmware: {err}"
        ) from err
    except TypeError as err:
        raise ConfigEntryNotReady(
            f"Invalid response ISY, device is likely still starting: {err}"
        ) from err

    isy_data = entry.runtime_data = IsyData()
    _categorize_nodes(isy_data, isy.nodes, ignore_identifier, sensor_identifier)
    _categorize_programs(isy_data, isy.programs)
    # Gather ISY Variables to be added.
    if isy.variables.children:
        isy_data.devices[CONF_VARIABLES] = _create_service_device_info(
            isy, name=CONF_VARIABLES.title(), unique_id=CONF_VARIABLES
        )
        numbers = isy_data.variables[Platform.NUMBER]
        for vtype, _, vid in isy.variables.children:
            numbers.append(isy.variables[vtype][vid])
    if (
        isy.conf[CONFIG_NETWORKING] or isy.conf.get(CONFIG_PORTAL)
    ) and isy.networking.nobjs:
        isy_data.devices[CONF_NETWORK] = _create_service_device_info(
            isy, name=CONFIG_NETWORKING, unique_id=CONF_NETWORK
        )
        for resource in isy.networking.nobjs:
            isy_data.net_resources.append(resource)

    # Dump ISY Clock Information. Future: Add ISY as sensor to Hass with attrs
    _LOGGER.debug(repr(isy.clock))

    isy_data.root = isy
    _async_get_or_create_isy_device_in_registry(hass, entry, isy)

    # Load platforms for the devices in the ISY controller that we support.
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Clean-up any old entities that we no longer provide.
    _async_cleanup_registry_entries(hass, entry)

    @callback
    def _async_stop_auto_update(event: Event) -> None:
        """Stop the isy auto update on Home Assistant Shutdown."""
        _LOGGER.debug("ISY Stopping Event Stream and automatic updates")
        isy.websocket.stop()

    _LOGGER.debug("ISY Starting Event Stream and automatic updates")
    isy.websocket.start()

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _async_stop_auto_update)
    )

    return True