async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Firmata domain."""
    # Delete specific entries that no longer exist in the config
    if hass.config_entries.async_entries(DOMAIN):
        for entry in hass.config_entries.async_entries(DOMAIN):
            remove = True
            for board in config[DOMAIN]:
                if entry.data[CONF_SERIAL_PORT] == board[CONF_SERIAL_PORT]:
                    remove = False
                    break
            if remove:
                await hass.config_entries.async_remove(entry.entry_id)

    # Setup new entries and update old entries
    for board in config[DOMAIN]:
        firmata_config = copy(board)
        existing_entry = False
        for entry in hass.config_entries.async_entries(DOMAIN):
            if board[CONF_SERIAL_PORT] == entry.data[CONF_SERIAL_PORT]:
                existing_entry = True
                firmata_config[CONF_NAME] = entry.data[CONF_NAME]
                hass.config_entries.async_update_entry(entry, data=firmata_config)
                break
        if not existing_entry:
            hass.async_create_task(
                hass.config_entries.flow.async_init(
                    DOMAIN,
                    context={"source": SOURCE_IMPORT},
                    data=firmata_config,
                )
            )

    return True