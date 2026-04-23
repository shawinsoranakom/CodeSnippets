async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up an Insteon entry."""

    if dev_path := entry.options.get(CONF_DEV_PATH):
        hass.data[DOMAIN] = {}
        hass.data[DOMAIN][CONF_DEV_PATH] = dev_path

    api.async_load_api(hass)
    await api.async_register_insteon_frontend(hass)

    if not devices.modem:
        try:
            await async_connect(**entry.data)
        except ConnectionError as exception:
            _LOGGER.error("Could not connect to Insteon modem")
            raise ConfigEntryNotReady from exception

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, close_insteon_connection)
    )

    await devices.async_load(
        workdir=hass.config.config_dir, id_devices=0, load_modem_aldb=0
    )

    # If options existed in YAML and have not already been saved to the config entry
    # add them now
    if (
        not entry.options
        and entry.source == SOURCE_IMPORT
        and hass.data.get(DOMAIN)
        and hass.data[DOMAIN].get(OPTIONS)
    ):
        hass.config_entries.async_update_entry(
            entry=entry,
            options=hass.data[DOMAIN][OPTIONS],
        )

    for device_override in entry.options.get(CONF_OVERRIDE, []):
        # Override the device default capabilities for a specific address
        address = device_override.get("address")
        if not devices.get(address):
            cat = device_override[CONF_CAT]
            subcat = device_override[CONF_SUBCAT]
            devices.set_id(address, cat, subcat, 0)

    for device in entry.options.get(CONF_X10, []):
        housecode = device.get(CONF_HOUSECODE)
        unitcode = device.get(CONF_UNITCODE)
        x10_type = "on_off"
        steps = device.get(CONF_DIM_STEPS, 22)
        if device.get(CONF_PLATFORM) == "light":
            x10_type = "dimmable"
        elif device.get(CONF_PLATFORM) == "binary_sensor":
            x10_type = "sensor"
        _LOGGER.debug(
            "Adding X10 device to Insteon: %s %d %s", housecode, unitcode, x10_type
        )
        device = devices.add_x10_device(housecode, unitcode, x10_type, steps)

    await hass.config_entries.async_forward_entry_setups(entry, INSTEON_PLATFORMS)

    for address in devices:
        device = devices[address]
        platforms = get_device_platforms(device)
        add_insteon_events(hass, device)
        if not platforms:
            create_insteon_device(hass, device, entry.entry_id)

    _LOGGER.debug("Insteon device count: %s", len(devices))
    register_new_device_callback(hass)
    async_setup_services(hass)

    create_insteon_device(hass, devices.modem, entry.entry_id)

    entry.async_create_background_task(
        hass, async_get_device_config(hass, entry), "insteon-get-device-config"
    )

    return True