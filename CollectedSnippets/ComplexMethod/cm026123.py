async def websocket_update_zha_configuration(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Update the ZHA configuration."""
    config_entry: ConfigEntry = get_config_entry(hass)
    options = config_entry.options
    data_to_save = {**options, CUSTOM_CONFIGURATION: msg["data"]}

    for section, schema in ZHA_CONFIG_SCHEMAS.items():
        for entry in schema.schema:
            # remove options that match defaults
            if (
                data_to_save[CUSTOM_CONFIGURATION].get(section, {}).get(entry)
                == entry.default()
            ):
                data_to_save[CUSTOM_CONFIGURATION][section].pop(entry)
            # remove entire section block if empty
            if (
                not data_to_save[CUSTOM_CONFIGURATION].get(section)
                and section in data_to_save[CUSTOM_CONFIGURATION]
            ):
                data_to_save[CUSTOM_CONFIGURATION].pop(section)

    # remove entire custom_configuration block if empty
    if (
        not data_to_save.get(CUSTOM_CONFIGURATION)
        and CUSTOM_CONFIGURATION in data_to_save
    ):
        data_to_save.pop(CUSTOM_CONFIGURATION)

    _LOGGER.info(
        "Updating ZHA custom configuration options from %s to %s",
        options,
        data_to_save,
    )

    hass.config_entries.async_update_entry(config_entry, options=data_to_save)
    status = await hass.config_entries.async_reload(config_entry.entry_id)
    connection.send_result(msg[ID], status)