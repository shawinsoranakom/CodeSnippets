async def async_setup_entry(hass: HomeAssistant, entry: SenseConfigEntry) -> bool:
    """Set up Sense from a config entry."""

    entry_data = entry.data
    timeout = entry_data[CONF_TIMEOUT]

    access_token = entry_data.get("access_token", "")
    user_id = entry_data.get("user_id", "")
    device_id = entry_data.get("device_id", "")
    refresh_token = entry_data.get("refresh_token", "")
    monitor_id = entry_data.get("monitor_id", "")

    client_session = async_get_clientsession(hass)

    # Creating the AsyncSenseable object loads
    # ssl certificates which does blocking IO
    gateway = await hass.async_add_executor_job(
        partial(
            ASyncSenseable,
            api_timeout=timeout,
            wss_timeout=timeout,
            client_session=client_session,
        )
    )
    gateway.rate_limit = ACTIVE_UPDATE_RATE

    try:
        gateway.load_auth(access_token, user_id, device_id, refresh_token)
        gateway.set_monitor_id(monitor_id)
        await gateway.get_monitor_data()
    except (SenseAuthenticationException, SenseMFARequiredException) as err:
        _LOGGER.warning("Sense authentication expired")
        raise ConfigEntryAuthFailed(err) from err
    except SENSE_TIMEOUT_EXCEPTIONS as err:
        raise ConfigEntryNotReady(
            str(err) or "Timed out during authentication"
        ) from err
    except SENSE_CONNECT_EXCEPTIONS as err:
        raise ConfigEntryNotReady(str(err)) from err

    try:
        await gateway.fetch_devices()
        await gateway.update_realtime()
    except SENSE_TIMEOUT_EXCEPTIONS as err:
        raise ConfigEntryNotReady(
            str(err) or "Timed out during realtime update"
        ) from err
    except SENSE_WEBSOCKET_EXCEPTIONS as err:
        raise ConfigEntryNotReady(str(err) or "Error during realtime update") from err

    trends_coordinator = SenseTrendCoordinator(hass, entry, gateway)
    realtime_coordinator = SenseRealtimeCoordinator(hass, entry, gateway)

    # This can take longer than 60s and we already know
    # sense is online since get_discovered_device_data was
    # successful so we do it later.
    entry.async_create_background_task(
        hass,
        trends_coordinator.async_request_refresh(),
        "sense.trends-coordinator-refresh",
    )
    entry.async_create_background_task(
        hass,
        realtime_coordinator.async_request_refresh(),
        "sense.realtime-coordinator-refresh",
    )

    entry.runtime_data = SenseData(
        data=gateway,
        trends=trends_coordinator,
        rt=realtime_coordinator,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True