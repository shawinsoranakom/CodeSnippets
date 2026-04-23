async def async_attach_trigger(
    hass: HomeAssistant,
    config: ConfigType,
    action: TriggerActionType,
    trigger_info: TriggerInfo,
) -> CALLBACK_TYPE:
    """Attach a trigger."""
    if config[CONF_TYPE] not in TRIGGER_TYPES:
        return await entity.async_attach_trigger(hass, config, action, trigger_info)
    if config[CONF_TYPE] == "buffering":
        to_state = STATE_BUFFERING
    elif config[CONF_TYPE] == "idle":
        to_state = STATE_IDLE
    elif config[CONF_TYPE] == "turned_off":
        to_state = STATE_OFF
    elif config[CONF_TYPE] == "turned_on":
        to_state = STATE_ON
    elif config[CONF_TYPE] == "paused":
        to_state = STATE_PAUSED
    else:  # "playing"
        to_state = STATE_PLAYING

    state_config = {
        CONF_PLATFORM: "state",
        CONF_ENTITY_ID: config[CONF_ENTITY_ID],
        state_trigger.CONF_TO: to_state,
    }
    if CONF_FOR in config:
        state_config[CONF_FOR] = config[CONF_FOR]
    state_config = await state_trigger.async_validate_trigger_config(hass, state_config)
    return await state_trigger.async_attach_trigger(
        hass, state_config, action, trigger_info, platform_type="device"
    )