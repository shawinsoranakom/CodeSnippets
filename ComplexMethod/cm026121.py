async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up ZHA.

    Will automatically load components to support devices found on the network.
    """

    # Try to perform an in-place migration if we detect that the device path can be made
    # unique
    device_path = config_entry.data[CONF_DEVICE][CONF_DEVICE_PATH]
    usb_device = await hass.async_add_executor_job(usb_device_from_path, device_path)

    if usb_device is not None and device_path != usb_device.device:
        _LOGGER.info(
            "Migrating ZHA device path from %s to %s", device_path, usb_device.device
        )
        new_data = {**config_entry.data}
        new_data[CONF_DEVICE][CONF_DEVICE_PATH] = usb_device.device
        hass.config_entries.async_update_entry(config_entry, data=new_data)
        device_path = usb_device.device

    ha_zha_data: HAZHAData = get_zha_data(hass)
    ha_zha_data.config_entry = config_entry
    zha_lib_data: ZHAData = create_zha_config(hass, ha_zha_data)

    zha_gateway = await Gateway.async_from_config(zha_lib_data)

    # Load and cache device trigger information early
    device_registry = dr.async_get(hass)
    radio_mgr = ZhaRadioManager.from_config_entry(hass, config_entry)

    async with radio_mgr.create_zigpy_app(connect=False) as app:
        for dev in app.devices.values():
            dev_entry = device_registry.async_get_device(
                identifiers={(DOMAIN, str(dev.ieee))},
                connections={(dr.CONNECTION_ZIGBEE, str(dev.ieee))},
            )

            if dev_entry is None:
                continue

            zha_lib_data.device_trigger_cache[dev_entry.id] = (
                str(dev.ieee),
                get_device_automation_triggers(dev),
            )
        ha_zha_data.device_trigger_cache = zha_lib_data.device_trigger_cache

    _LOGGER.debug("Trigger cache: %s", zha_lib_data.device_trigger_cache)

    # Check if firmware update is in progress for this device
    _raise_if_port_in_use(hass, device_path)

    try:
        await zha_gateway.async_initialize()
    except NetworkSettingsInconsistent as exc:
        await warn_on_inconsistent_network_settings(
            hass,
            config_entry=config_entry,
            old_state=exc.old_state,
            new_state=exc.new_state,
        )
        raise ConfigEntryError(
            "Network settings do not match most recent backup"
        ) from exc
    except TransientConnectionError as exc:
        raise ConfigEntryNotReady from exc
    except Exception as exc:
        _LOGGER.debug("Failed to set up ZHA", exc_info=exc)
        _raise_if_port_in_use(hass, device_path)

        if (
            not device_path.startswith("socket://")
            and RadioType[config_entry.data[CONF_RADIO_TYPE]] == RadioType.ezsp
        ):
            try:
                # Ignore all exceptions during probing, they shouldn't halt setup
                if await warn_on_wrong_silabs_firmware(hass, device_path):
                    raise ConfigEntryError("Incorrect firmware installed") from exc
            except AlreadyRunningEZSP as ezsp_exc:
                raise ConfigEntryNotReady from ezsp_exc

        raise ConfigEntryNotReady from exc

    repairs.async_delete_blocking_issues(hass)

    # Set unique_id if it was not migrated previously
    if not config_entry.unique_id or not config_entry.unique_id.startswith("epid="):
        unique_id = get_config_entry_unique_id(zha_gateway.state.network_info)
        hass.config_entries.async_update_entry(config_entry, unique_id=unique_id)

    ha_zha_data.gateway_proxy = ZHAGatewayProxy(hass, config_entry, zha_gateway)

    manufacturer = zha_gateway.state.node_info.manufacturer
    model = zha_gateway.state.node_info.model

    if manufacturer is None and model is None:
        manufacturer = "Unknown"
        model = "Unknown"

    device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_ZIGBEE, str(zha_gateway.state.node_info.ieee))},
        identifiers={(DOMAIN, str(zha_gateway.state.node_info.ieee))},
        name="Zigbee Coordinator",
        manufacturer=manufacturer,
        model=model,
        sw_version=zha_gateway.state.node_info.version,
    )

    websocket_api.async_load_api(hass)

    async def async_shutdown(_: Event) -> None:
        """Handle shutdown tasks."""
        assert ha_zha_data.gateway_proxy is not None
        await ha_zha_data.gateway_proxy.shutdown()

    config_entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, async_shutdown)
    )

    @callback
    def update_config(event: Event) -> None:
        """Handle Core config update."""
        zha_gateway.config.local_timezone = ZoneInfo(hass.config.time_zone)
        zha_gateway.config.country_code = hass.config.country

    config_entry.async_on_unload(
        hass.bus.async_listen(EVENT_CORE_CONFIG_UPDATE, update_config)
    )

    if fw_info := homeassistant_hardware.get_firmware_info(hass, config_entry):
        await async_notify_firmware_info(
            hass,
            DOMAIN,
            firmware_info=fw_info,
        )

    await ha_zha_data.gateway_proxy.async_initialize_devices_and_entities()
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    async_dispatcher_send(hass, SIGNAL_ADD_ENTITIES)
    return True