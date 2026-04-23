async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    if config_entry.version == 1:
        data = {
            CONF_RADIO_TYPE: config_entry.data[CONF_RADIO_TYPE],
            CONF_DEVICE: {CONF_DEVICE_PATH: config_entry.data[CONF_USB_PATH]},
        }

        baudrate = get_zha_data(hass).yaml_config.get(CONF_BAUDRATE)
        if data[CONF_RADIO_TYPE] != RadioType.deconz and baudrate in BAUD_RATES:
            data[CONF_DEVICE][CONF_BAUDRATE] = baudrate

        hass.config_entries.async_update_entry(config_entry, data=data, version=2)

    if config_entry.version == 2:
        data = {**config_entry.data}

        if data[CONF_RADIO_TYPE] == "ti_cc":
            data[CONF_RADIO_TYPE] = "znp"

        hass.config_entries.async_update_entry(config_entry, data=data, version=3)

    if config_entry.version == 3:
        data = {**config_entry.data}

        if not data[CONF_DEVICE].get(CONF_BAUDRATE):
            data[CONF_DEVICE][CONF_BAUDRATE] = {
                "deconz": 38400,
                "xbee": 57600,
                "ezsp": 57600,
                "znp": 115200,
                "zigate": 115200,
            }[data[CONF_RADIO_TYPE]]

        if not data[CONF_DEVICE].get(CONF_FLOW_CONTROL):
            data[CONF_DEVICE][CONF_FLOW_CONTROL] = None

        hass.config_entries.async_update_entry(config_entry, data=data, version=4)

    if config_entry.version == 4:
        radio_mgr = ZhaRadioManager.from_config_entry(hass, config_entry)
        await radio_mgr.async_read_backups_from_database()

        if radio_mgr.backups:
            # We migrate all ZHA config entries to use a `unique_id` specific to the
            # Zigbee network, not to the hardware
            backup = radio_mgr.backups[0]
            hass.config_entries.async_update_entry(
                config_entry,
                unique_id=get_config_entry_unique_id(backup.network_info),
                version=5,
            )
        else:
            # If no backups are available, the unique_id will be set when the network is
            # loaded during setup
            hass.config_entries.async_update_entry(
                config_entry,
                version=5,
            )

    _LOGGER.info("Migration to version %s successful", config_entry.version)
    return True