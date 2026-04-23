async def async_setup_entry(hass: HomeAssistant, entry: NutConfigEntry) -> bool:
    """Set up Network UPS Tools (NUT) from a config entry."""

    # strip out the stale options CONF_RESOURCES,
    # maintain the entry in data in case of version rollback
    if CONF_RESOURCES in entry.options:
        new_data = {**entry.data, CONF_RESOURCES: entry.options[CONF_RESOURCES]}
        new_options = {k: v for k, v in entry.options.items() if k != CONF_RESOURCES}
        hass.config_entries.async_update_entry(
            entry, data=new_data, options=new_options
        )

    config = entry.data
    host = config[CONF_HOST]
    port = config[CONF_PORT]

    alias = config.get(CONF_ALIAS)
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    if CONF_SCAN_INTERVAL in entry.options:
        current_options = {**entry.options}
        current_options.pop(CONF_SCAN_INTERVAL)
        hass.config_entries.async_update_entry(entry, options=current_options)

    data = PyNUTData(host, port, alias, username, password)

    entry.async_on_unload(data.async_shutdown)

    coordinator = NutCoordinator(hass, data, entry)

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_config_entry_first_refresh()

    # Note that async_listen_once is not used here because the listener
    # could be removed after the event is fired.
    entry.async_on_unload(
        hass.bus.async_listen(EVENT_HOMEASSISTANT_STOP, data.async_shutdown)
    )
    status = coordinator.data

    _LOGGER.debug("NUT Sensors Available: %s", status or None)

    unique_id = _unique_id_from_status(status)
    if unique_id is None:
        unique_id = entry.entry_id

    elif entry.unique_id is None:
        hass.config_entries.async_update_entry(entry, unique_id=unique_id)

    if username is not None and password is not None:
        # Dynamically add outlet integration commands
        additional_integration_commands = set()
        if (num_outlets := status.get("outlet.count")) is not None:
            for outlet_num in range(1, int(num_outlets) + 1):
                outlet_num_str: str = str(outlet_num)
                additional_integration_commands |= {
                    f"outlet.{outlet_num_str}.load.cycle",
                    f"outlet.{outlet_num_str}.load.on",
                    f"outlet.{outlet_num_str}.load.off",
                }

        valid_integration_commands = (
            INTEGRATION_SUPPORTED_COMMANDS | additional_integration_commands
        )

        user_available_commands = {
            device_command
            for device_command in await data.async_list_commands() or {}
            if device_command in valid_integration_commands
        }
    else:
        user_available_commands = set()

    _LOGGER.debug(
        "NUT Commands Available: %s",
        user_available_commands or None,
    )

    entry.runtime_data = NutRuntimeData(
        coordinator, data, unique_id, user_available_commands
    )

    connections: set[tuple[str, str]] | None = None
    if data.device_info.mac_address is not None:
        connections = {(CONNECTION_NETWORK_MAC, data.device_info.mac_address)}

    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, unique_id)},
        connections=connections,
        name=data.name.title(),
        manufacturer=data.device_info.manufacturer,
        model=data.device_info.model,
        model_id=data.device_info.model_id,
        sw_version=data.device_info.firmware,
        serial_number=data.device_info.serial,
        suggested_area=data.device_info.device_location,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True