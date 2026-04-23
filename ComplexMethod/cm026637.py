async def async_call_action_from_config(
    hass: HomeAssistant,
    config: ConfigType,
    variables: TemplateVarsType,
    context: Context | None,
) -> None:
    """Execute a device action."""
    service_data = {ATTR_ENTITY_ID: config[CONF_ENTITY_ID]}
    if CONF_CODE in config:
        service_data[ATTR_CODE] = config[CONF_CODE]

    if config[CONF_TYPE] == "arm_away":
        service = SERVICE_ALARM_ARM_AWAY
    elif config[CONF_TYPE] == "arm_home":
        service = SERVICE_ALARM_ARM_HOME
    elif config[CONF_TYPE] == "arm_night":
        service = SERVICE_ALARM_ARM_NIGHT
    elif config[CONF_TYPE] == "arm_vacation":
        service = SERVICE_ALARM_ARM_VACATION
    elif config[CONF_TYPE] == "disarm":
        service = SERVICE_ALARM_DISARM
    elif config[CONF_TYPE] == "trigger":
        service = SERVICE_ALARM_TRIGGER

    await hass.services.async_call(
        DOMAIN, service, service_data, blocking=True, context=context
    )