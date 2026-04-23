async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Matter from a config entry."""
    if use_addon := entry.data.get(CONF_USE_ADDON):
        await _async_ensure_addon_running(hass, entry)

    matter_client = MatterClient(entry.data[CONF_URL], async_get_clientsession(hass))
    try:
        async with asyncio.timeout(CONNECT_TIMEOUT):
            await matter_client.connect()
    except (CannotConnect, TimeoutError) as err:
        raise ConfigEntryNotReady("Failed to connect to matter server") from err
    except InvalidServerVersion as err:
        if isinstance(err, ServerVersionTooOld):
            if use_addon:
                addon_manager = _get_addon_manager(hass)
                addon_manager.async_schedule_update_addon(catch_error=True)
            else:
                async_create_issue(
                    hass,
                    DOMAIN,
                    "server_version_version_too_old",
                    is_fixable=False,
                    severity=IssueSeverity.ERROR,
                    translation_key="server_version_version_too_old",
                )
        elif isinstance(err, ServerVersionTooNew):
            async_create_issue(
                hass,
                DOMAIN,
                "server_version_version_too_new",
                is_fixable=False,
                severity=IssueSeverity.ERROR,
                translation_key="server_version_version_too_new",
            )
        raise ConfigEntryNotReady(f"Invalid server version: {err}") from err

    except Exception as err:
        LOGGER.exception("Failed to connect to matter server")
        raise ConfigEntryNotReady(
            "Unknown error connecting to the Matter server"
        ) from err

    async_delete_issue(hass, DOMAIN, "server_version_version_too_old")
    async_delete_issue(hass, DOMAIN, "server_version_version_too_new")

    async def on_hass_stop(event: Event) -> None:
        """Handle incoming stop event from Home Assistant."""
        await matter_client.disconnect()

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, on_hass_stop)
    )

    async_register_api(hass)

    # launch the matter client listen task in the background
    # use the init_ready event to wait until initialization is done
    init_ready = asyncio.Event()
    listen_task = asyncio.create_task(
        _client_listen(hass, entry, matter_client, init_ready)
    )

    try:
        async with asyncio.timeout(LISTEN_READY_TIMEOUT):
            await init_ready.wait()
    except TimeoutError as err:
        listen_task.cancel()
        raise ConfigEntryNotReady("Matter client not ready") from err

    # Set default fabric
    try:
        await matter_client.set_default_fabric_label(
            hass.config.location_name or "Home"
        )
    except (NotConnected, MatterError) as err:
        listen_task.cancel()
        raise ConfigEntryNotReady("Failed to set default fabric label") from err

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    # create an intermediate layer (adapter) which keeps track of the nodes
    # and discovery of platform entities from the node attributes
    matter = MatterAdapter(hass, matter_client, entry)
    hass.data[DOMAIN][entry.entry_id] = MatterEntryData(matter, listen_task)

    await hass.config_entries.async_forward_entry_setups(entry, SUPPORTED_PLATFORMS)
    await matter.setup_nodes()

    # If the listen task is already failed, we need to raise ConfigEntryNotReady
    if listen_task.done() and (listen_error := listen_task.exception()) is not None:
        await hass.config_entries.async_unload_platforms(entry, SUPPORTED_PLATFORMS)
        hass.data[DOMAIN].pop(entry.entry_id)
        try:
            await matter_client.disconnect()
        finally:
            raise ConfigEntryNotReady(listen_error) from listen_error

    return True