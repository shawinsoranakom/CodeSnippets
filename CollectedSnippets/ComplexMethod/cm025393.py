async def async_setup_entry(hass: HomeAssistant, entry: MyNeomitisConfigEntry) -> bool:
    """Set up MyNeomitis from a config entry."""
    session = async_get_clientsession(hass)

    email: str = entry.data[CONF_EMAIL]
    password: str = entry.data[CONF_PASSWORD]

    api = pyaxencoapi.PyAxencoAPI(session)
    connected = False
    try:
        await api.login(email, password)
        await api.connect_websocket()
        connected = True
        _LOGGER.debug("Successfully connected to Login/WebSocket")

        # Retrieve the user's devices
        devices: list[dict[str, Any]] = await api.get_devices()

    except aiohttp.ClientResponseError as err:
        if connected:
            try:
                await api.disconnect_websocket()
            except (
                TimeoutError,
                ConnectionError,
                aiohttp.ClientError,
            ) as disconnect_err:
                _LOGGER.error(
                    "Error while disconnecting WebSocket for %s: %s",
                    entry.entry_id,
                    disconnect_err,
                )
        if err.status == 401:
            raise ConfigEntryAuthFailed(
                "Authentication failed, please update your credentials"
            ) from err
        raise ConfigEntryNotReady(f"Error connecting to API: {err}") from err
    except (TimeoutError, ConnectionError, aiohttp.ClientError) as err:
        if connected:
            try:
                await api.disconnect_websocket()
            except (
                TimeoutError,
                ConnectionError,
                aiohttp.ClientError,
            ) as disconnect_err:
                _LOGGER.error(
                    "Error while disconnecting WebSocket for %s: %s",
                    entry.entry_id,
                    disconnect_err,
                )
        raise ConfigEntryNotReady(f"Error connecting to API/WebSocket: {err}") from err

    entry.runtime_data = MyNeomitisRuntimeData(api=api, devices=devices)

    async def _async_disconnect_websocket(_event: Event) -> None:
        """Disconnect WebSocket on Home Assistant shutdown."""
        try:
            await api.disconnect_websocket()
        except (TimeoutError, ConnectionError, aiohttp.ClientError) as err:
            _LOGGER.error(
                "Error while disconnecting WebSocket for %s: %s",
                entry.entry_id,
                err,
            )

    entry.async_on_unload(
        hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STOP, _async_disconnect_websocket
        )
    )

    # Load platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True