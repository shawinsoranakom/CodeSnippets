async def async_setup_entry(hass: HomeAssistant, entry: ZwaveJSConfigEntry) -> bool:
    """Set up Z-Wave JS from a config entry."""
    if use_addon := entry.data.get(CONF_USE_ADDON):
        await async_ensure_addon_running(hass, entry)

    client = ZwaveClient(
        entry.data[CONF_URL],
        async_get_clientsession(hass),
        additional_user_agent_components=USER_AGENT,
    )

    # connect and throw error if connection failed
    try:
        async with asyncio.timeout(CONNECT_TIMEOUT):
            await client.connect()
    except InvalidServerVersion as err:
        if use_addon:
            addon_manager = _get_addon_manager(hass)
            addon_manager.async_schedule_update_addon(catch_error=True)
        else:
            async_create_issue(
                hass,
                DOMAIN,
                "invalid_server_version",
                is_fixable=False,
                severity=IssueSeverity.ERROR,
                translation_key="invalid_server_version",
            )
        raise ConfigEntryNotReady(f"Invalid server version: {err}") from err
    except (TimeoutError, BaseZwaveJSServerError) as err:
        raise ConfigEntryNotReady(f"Failed to connect: {err}") from err

    async_delete_issue(hass, DOMAIN, "invalid_server_version")
    LOGGER.debug("Connected to Zwave JS Server")

    # Set up websocket API
    async_register_api(hass)

    driver_ready = asyncio.Event()
    listen_task = entry.async_create_background_task(
        hass,
        client_listen(hass, entry, client, driver_ready),
        f"{DOMAIN}_{entry.title}_client_listen",
    )

    entry.async_on_unload(client.disconnect)

    async def handle_ha_shutdown(event: Event) -> None:
        """Handle HA shutdown."""
        await client.disconnect()

    entry.async_on_unload(
        hass.bus.async_listen(EVENT_HOMEASSISTANT_STOP, handle_ha_shutdown)
    )

    driver_ready_task = entry.async_create_task(
        hass,
        driver_ready.wait(),
        f"{DOMAIN}_{entry.title}_driver_ready",
    )
    done, pending = await asyncio.wait(
        (driver_ready_task, listen_task),
        return_when=asyncio.FIRST_COMPLETED,
        timeout=DRIVER_READY_TIMEOUT,
    )

    if driver_ready_task in pending or listen_task in done:
        error_message = "Driver ready timed out"
        listen_error: BaseException | None = None
        if listen_task.done():
            listen_error, error_message = _get_listen_task_error(listen_task)
        else:
            listen_task.cancel()
        driver_ready_task.cancel()
        raise ConfigEntryNotReady(error_message) from listen_error

    LOGGER.debug("Connection to Zwave JS Server initialized")

    driver_events = DriverEvents(hass, entry)
    entry_runtime_data = ZwaveJSData(
        client=client,
        driver_events=driver_events,
    )
    entry.runtime_data = entry_runtime_data

    driver = client.driver
    # When the driver is ready we know it's set on the client.
    assert driver is not None

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    with contextlib.suppress(NotConnected):
        # If the client isn't connected the listen task may have an exception
        # and we'll handle the clean up below.
        await driver_events.setup(driver)

    # If the listen task is already failed, we need to raise ConfigEntryNotReady
    if listen_task.done():
        listen_error, error_message = _get_listen_task_error(listen_task)
        await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
        raise ConfigEntryNotReady(error_message) from listen_error

    # Re-attach trigger listeners.
    # Schedule this call to make sure the config entry is loaded first.

    @callback
    def on_config_entry_loaded() -> None:
        """Signal that server connection and driver are ready."""
        if entry.state is ConfigEntryState.LOADED:
            async_dispatcher_send(
                hass,
                f"{DOMAIN}_{driver.controller.home_id}_connected_to_server",
            )

    entry.async_on_unload(entry.async_on_state_change(on_config_entry_loaded))

    return True