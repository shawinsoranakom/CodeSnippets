async def webhook_register_sensor(
    hass: HomeAssistant, config_entry: ConfigEntry, data: dict[str, Any]
) -> Response:
    """Handle a register sensor webhook."""
    entity_type: str = data[ATTR_SENSOR_TYPE]
    unique_id: str = data[ATTR_SENSOR_UNIQUE_ID]
    device_name: str = config_entry.data[ATTR_DEVICE_NAME]

    unique_store_key = _gen_unique_id(config_entry.data[CONF_WEBHOOK_ID], unique_id)
    entity_registry = er.async_get(hass)
    existing_sensor = entity_registry.async_get_entity_id(
        entity_type, DOMAIN, unique_store_key
    )

    data[CONF_WEBHOOK_ID] = config_entry.data[CONF_WEBHOOK_ID]

    # If sensor already is registered, update current state instead
    if existing_sensor:
        _LOGGER.debug(
            "Re-register for %s of existing sensor %s", device_name, unique_id
        )

        entry = entity_registry.async_get(existing_sensor)
        assert entry is not None
        changes: dict[str, Any] = {}

        if (
            new_name := f"{device_name} {data[ATTR_SENSOR_NAME]}"
        ) != entry.original_name:
            changes["original_name"] = new_name

        if (
            should_be_disabled := data.get(ATTR_SENSOR_DISABLED)
        ) is None or should_be_disabled == entry.disabled:
            pass
        elif should_be_disabled:
            changes["disabled_by"] = er.RegistryEntryDisabler.INTEGRATION
        else:
            changes["disabled_by"] = None

        for ent_reg_key, data_key in (
            ("device_class", ATTR_SENSOR_DEVICE_CLASS),
            ("unit_of_measurement", ATTR_SENSOR_UOM),
            ("entity_category", ATTR_SENSOR_ENTITY_CATEGORY),
            ("original_icon", ATTR_SENSOR_ICON),
        ):
            if data_key in data and getattr(entry, ent_reg_key) != data[data_key]:
                changes[ent_reg_key] = data[data_key]

        if changes:
            entity_registry.async_update_entity(existing_sensor, **changes)

        _async_update_sensor_entity(
            hass, entity_type=entity_type, unique_store_key=unique_store_key, data=data
        )
    else:
        data[CONF_UNIQUE_ID] = unique_store_key
        data[CONF_NAME] = (
            f"{config_entry.data[ATTR_DEVICE_NAME]} {data[ATTR_SENSOR_NAME]}"
        )

        register_signal = f"{DOMAIN}_{entity_type}_register"
        async_dispatcher_send(hass, register_signal, data)

    return webhook_response(
        {"success": True},
        registration=config_entry.data,
        status=HTTPStatus.CREATED,
    )