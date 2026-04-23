async def websocket_delete_entity(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
    config_entry: LcnConfigEntry,
) -> None:
    """Delete an entity."""
    entity_config = next(
        (
            entity_config
            for entity_config in config_entry.data[CONF_ENTITIES]
            if (
                tuple(entity_config[CONF_ADDRESS]) == msg[CONF_ADDRESS]
                and entity_config[CONF_DOMAIN] == msg[CONF_DOMAIN]
                and get_resource(
                    entity_config[CONF_DOMAIN], entity_config[CONF_DOMAIN_DATA]
                )
                == get_resource(msg[CONF_DOMAIN], msg[CONF_DOMAIN_DATA])
            )
        ),
        None,
    )

    if entity_config is None:
        connection.send_result(msg["id"], False)
        return

    entity_configs = [
        ec for ec in config_entry.data[CONF_ENTITIES] if ec != entity_config
    ]
    data = {**config_entry.data, CONF_ENTITIES: entity_configs}

    hass.config_entries.async_update_entry(config_entry, data=data)

    # cleanup registries
    purge_entity_registry(hass, config_entry.entry_id, data)
    purge_device_registry(hass, config_entry.entry_id, data)

    connection.send_result(msg["id"])