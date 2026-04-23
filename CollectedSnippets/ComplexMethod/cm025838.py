def get_plug_devices(hass, entity_configs):
    """Produce list of plug devices from config entities."""
    for entity_id, entity_config in entity_configs.items():
        if (state := hass.states.get(entity_id)) is None:
            continue
        name = entity_config.get(CONF_NAME, state.name)

        if state.state == STATE_ON or state.domain == SENSOR_DOMAIN:
            if CONF_POWER in entity_config:
                power_val = entity_config[CONF_POWER]
                if isinstance(power_val, (float, int)):
                    power = float(power_val)
                elif isinstance(power_val, str):
                    power = float(hass.states.get(power_val).state)
                elif isinstance(power_val, Template):
                    power = float(power_val.async_render())
            elif state.domain == SENSOR_DOMAIN:
                power = float(state.state)
        else:
            power = 0.0
        last_changed = state.last_changed.timestamp()
        yield PlugInstance(
            entity_config[CONF_UNIQUE_ID],
            start_time=last_changed,
            alias=name,
            power=power,
        )