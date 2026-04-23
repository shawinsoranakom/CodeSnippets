def get_platforms(config_entry):
    """Return the platforms belonging to a config_entry."""
    model = config_entry.data[CONF_MODEL]
    flow_type = config_entry.data[CONF_FLOW_TYPE]

    if flow_type == CONF_GATEWAY:
        return GATEWAY_PLATFORMS
    if flow_type == CONF_DEVICE:
        if model in MODELS_SWITCH:
            return SWITCH_PLATFORMS
        if model in MODELS_HUMIDIFIER:
            return HUMIDIFIER_PLATFORMS
        if model in MODELS_FAN:
            return FAN_PLATFORMS
        if model in MODELS_LIGHT:
            return LIGHT_PLATFORMS
        for vacuum_model in MODELS_VACUUM:
            if model.startswith(vacuum_model):
                return VACUUM_PLATFORMS
        for air_monitor_model in MODELS_AIR_MONITOR:
            if model.startswith(air_monitor_model):
                return AIR_MONITOR_PLATFORMS
    _LOGGER.error(
        (
            "Unsupported device found! Please create an issue at "
            "https://github.com/syssi/xiaomi_airpurifier/issues "
            "and provide the following data: %s"
        ),
        model,
    )
    return []