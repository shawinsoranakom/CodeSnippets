async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Huawei LTE component from config entry."""
    url = entry.data[CONF_URL]

    def _connect() -> Connection:
        """Set up a connection."""
        kwargs: dict[str, Any] = {
            "timeout": CONNECTION_TIMEOUT,
        }
        if url.startswith("https://") and not entry.data.get(CONF_VERIFY_SSL):
            kwargs["requests_session"] = non_verifying_requests_session(url)
        if entry.options.get(CONF_UNAUTHENTICATED_MODE):
            _LOGGER.debug("Connecting in unauthenticated mode, reduced feature set")
            connection = Connection(url, **kwargs)
        else:
            _LOGGER.debug("Connecting in authenticated mode, full feature set")
            username = entry.data.get(CONF_USERNAME) or ""
            password = entry.data.get(CONF_PASSWORD) or ""
            connection = Connection(url, username=username, password=password, **kwargs)
        return connection

    try:
        connection = await hass.async_add_executor_job(_connect)
    except LoginErrorInvalidCredentialsException as ex:
        raise ConfigEntryAuthFailed from ex
    except Timeout as ex:
        raise ConfigEntryNotReady from ex

    # Set up router
    router = Router(hass, entry, connection, url)

    # Do initial data update
    await hass.async_add_executor_job(router.update)

    # Check that we found required information
    router_info = router.data.get(KEY_DEVICE_INFORMATION)
    if not entry.unique_id:
        # Transitional from < 2021.8: update None config entry and entity unique ids
        if router_info and (serial_number := router_info.get("SerialNumber")):
            hass.config_entries.async_update_entry(entry, unique_id=serial_number)
            ent_reg = er.async_get(hass)
            for entity_entry in er.async_entries_for_config_entry(
                ent_reg, entry.entry_id
            ):
                if not entity_entry.unique_id.startswith("None-"):
                    continue
                new_unique_id = entity_entry.unique_id.removeprefix("None-")
                new_unique_id = f"{serial_number}-{new_unique_id}"
                ent_reg.async_update_entity(
                    entity_entry.entity_id, new_unique_id=new_unique_id
                )
        else:
            await hass.async_add_executor_job(router.cleanup)
            msg = (
                "Could not resolve serial number to use as unique id for router at %s"
                ", setup failed"
            )
            if not entry.data.get(CONF_PASSWORD):
                msg += (
                    ". Try setting up credentials for the router for one startup, "
                    "unauthenticated mode can be enabled after that in integration "
                    "settings"
                )
            _LOGGER.error(msg, url)
            return False

    # Store reference to router
    hass.data[DOMAIN].routers[entry.entry_id] = router

    # Clear all subscriptions, enabled entities will push back theirs
    router.subscriptions.clear()

    # Update device MAC addresses on record. These can change due to toggling between
    # authenticated and unauthenticated modes, or likely also when enabling/disabling
    # SSIDs in the router config.
    try:
        wlan_settings = await hass.async_add_executor_job(
            router.client.wlan.multi_basic_settings
        )
    except Exception:  # noqa: BLE001
        # Assume not supported, or authentication required but in unauthenticated mode
        wlan_settings = {}
    macs = get_device_macs(router_info or {}, wlan_settings)
    # Be careful not to overwrite a previous, more complete set with a partial one
    if macs and (not entry.data[CONF_MAC] or (router_info and wlan_settings)):
        new_data = dict(entry.data)
        new_data[CONF_MAC] = macs
        hass.config_entries.async_update_entry(entry, data=new_data)

    # Set up device registry
    if router.device_identifiers or router.device_connections:
        device_info = DeviceInfo(
            configuration_url=router.url,
            connections=router.device_connections,
            identifiers=router.device_identifiers,
            manufacturer=entry.data.get(CONF_MANUFACTURER, DEFAULT_MANUFACTURER),
            name=router.device_name,
        )
        hw_version = None
        sw_version = None
        if router_info:
            hw_version = router_info.get("HardwareVersion")
            sw_version = router_info.get("SoftwareVersion")
            if router_info.get("DeviceName"):
                device_info[ATTR_MODEL] = router_info["DeviceName"]
        if not sw_version and router.data.get(KEY_DEVICE_BASIC_INFORMATION):
            sw_version = router.data[KEY_DEVICE_BASIC_INFORMATION].get(
                "SoftwareVersion"
            )
        if hw_version:
            device_info[ATTR_HW_VERSION] = hw_version
        if sw_version:
            device_info[ATTR_SW_VERSION] = sw_version
        device_registry = dr.async_get(hass)
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            **device_info,
        )

    # Forward config entry setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Notify doesn't support config entry setup yet, load with discovery for now
    await discovery.async_load_platform(
        hass,
        Platform.NOTIFY,
        DOMAIN,
        {
            ATTR_CONFIG_ENTRY_ID: entry.entry_id,
            CONF_NAME: entry.options.get(CONF_NAME, DEFAULT_NOTIFY_SERVICE_NAME),
            CONF_RECIPIENT: entry.options.get(CONF_RECIPIENT),
        },
        hass.data[DOMAIN].hass_config,
    )

    def _update_router(*_: Any) -> None:
        """Update router data.

        Separate passthrough function because lambdas don't work with track_time_interval.
        """
        router.update()

    # Set up periodic update
    entry.async_on_unload(
        async_track_time_interval(hass, _update_router, SCAN_INTERVAL)
    )

    # Clean up at end
    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, router.cleanup)
    )

    return True