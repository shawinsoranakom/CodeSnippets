async def async_setup_entry(hass: HomeAssistant, entry: LIFXConfigEntry) -> bool:
    """Set up LIFX from a config entry."""
    if async_entry_is_legacy(entry):
        return True

    if legacy_entry := async_get_legacy_entry(hass):
        # If the legacy entry still exists, harvest the entities
        # that are moving to this config entry.
        async_migrate_entities_devices(hass, legacy_entry.entry_id, entry)

    assert entry.unique_id is not None
    if DATA_LIFX_MANAGER not in hass.data:
        manager = LIFXManager(hass)
        hass.data[DATA_LIFX_MANAGER] = manager
        manager.async_setup()

    host = entry.data[CONF_HOST]
    connection = LIFXConnection(host, TARGET_ANY)
    try:
        await connection.async_setup()
    except socket.gaierror as ex:
        connection.async_stop()
        raise ConfigEntryNotReady(f"Could not resolve {host}: {ex}") from ex
    coordinator = LIFXUpdateCoordinator(hass, entry, connection)
    coordinator.async_setup()
    try:
        await coordinator.async_config_entry_first_refresh()
    except ConfigEntryNotReady:
        connection.async_stop()
        raise

    serial = formatted_serial(coordinator.serial_number)
    if serial != entry.unique_id:
        # If the serial number of the device does not match the unique_id
        # of the config entry, it likely means the DHCP lease has expired
        # and the device has been assigned a new IP address. We need to
        # wait for the next discovery to find the device at its new address
        # and update the config entry so we do not mix up devices.
        raise ConfigEntryNotReady(
            f"Unexpected device found at {host}; expected {entry.unique_id}, found {serial}"
        )
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True