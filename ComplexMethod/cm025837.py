async def validate_configs(hass, entity_configs):
    """Validate that entities exist and ensure templates are ready to use."""
    entity_registry = er.async_get(hass)
    for entity_id, entity_config in entity_configs.items():
        if (state := hass.states.get(entity_id)) is None:
            _LOGGER.debug("Entity not found: %s", entity_id)
            continue

        if entity := entity_registry.async_get(entity_id):
            entity_config[CONF_UNIQUE_ID] = get_system_unique_id(entity)
        else:
            entity_config[CONF_UNIQUE_ID] = entity_id

        if CONF_POWER in entity_config:
            power_val = entity_config[CONF_POWER]
            if isinstance(power_val, str) and is_template_string(power_val):
                entity_config[CONF_POWER] = Template(power_val, hass)
        elif CONF_POWER_ENTITY in entity_config:
            power_val = entity_config[CONF_POWER_ENTITY]
            if hass.states.get(power_val) is None:
                _LOGGER.debug("Sensor Entity not found: %s", power_val)
            else:
                entity_config[CONF_POWER] = power_val
        elif state.domain == SENSOR_DOMAIN:
            pass
        else:
            _LOGGER.debug("No power value defined for: %s", entity_id)