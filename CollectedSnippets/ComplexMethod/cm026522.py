async def async_call_action_from_config(
    hass: HomeAssistant,
    config: ConfigType,
    variables: TemplateVarsType,
    context: Context | None,
) -> None:
    """Execute a device action."""
    service_data = {ATTR_ENTITY_ID: config[CONF_ENTITY_ID]}

    if config[CONF_TYPE] == "open":
        service = SERVICE_OPEN_COVER
    elif config[CONF_TYPE] == "close":
        service = SERVICE_CLOSE_COVER
    elif config[CONF_TYPE] == "stop":
        service = SERVICE_STOP_COVER
    elif config[CONF_TYPE] == "open_tilt":
        service = SERVICE_OPEN_COVER_TILT
    elif config[CONF_TYPE] == "close_tilt":
        service = SERVICE_CLOSE_COVER_TILT
    elif config[CONF_TYPE] == "set_position":
        service = SERVICE_SET_COVER_POSITION
        service_data[ATTR_POSITION] = config["position"]
    elif config[CONF_TYPE] == "set_tilt_position":
        service = SERVICE_SET_COVER_TILT_POSITION
        service_data[ATTR_TILT_POSITION] = config["position"]

    await hass.services.async_call(
        DOMAIN, service, service_data, blocking=True, context=context
    )