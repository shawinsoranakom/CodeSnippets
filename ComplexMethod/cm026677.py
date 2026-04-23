async def async_attach_trigger(
    hass: HomeAssistant,
    config: ConfigType,
    action: TriggerActionType,
    trigger_info: TriggerInfo,
) -> CALLBACK_TYPE:
    """Attach a trigger."""
    if config[CONF_TYPE] == "jammed":
        to_state = LockState.JAMMED
    elif config[CONF_TYPE] == "opening":
        to_state = LockState.OPENING
    elif config[CONF_TYPE] == "locking":
        to_state = LockState.LOCKING
    elif config[CONF_TYPE] == "open":
        to_state = LockState.OPEN
    elif config[CONF_TYPE] == "unlocking":
        to_state = LockState.UNLOCKING
    elif config[CONF_TYPE] == "locked":
        to_state = LockState.LOCKED
    else:
        to_state = LockState.UNLOCKED

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