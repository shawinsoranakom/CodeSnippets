async def async_attach_trigger(
    hass: HomeAssistant,
    config: ConfigType,
    action: TriggerActionType,
    trigger_info: TriggerInfo,
) -> CALLBACK_TYPE:
    """Attach a trigger."""
    if config[CONF_TYPE] == "triggered":
        to_state = AlarmControlPanelState.TRIGGERED
    elif config[CONF_TYPE] == "disarmed":
        to_state = AlarmControlPanelState.DISARMED
    elif config[CONF_TYPE] == "arming":
        to_state = AlarmControlPanelState.ARMING
    elif config[CONF_TYPE] == "armed_home":
        to_state = AlarmControlPanelState.ARMED_HOME
    elif config[CONF_TYPE] == "armed_away":
        to_state = AlarmControlPanelState.ARMED_AWAY
    elif config[CONF_TYPE] == "armed_night":
        to_state = AlarmControlPanelState.ARMED_NIGHT
    elif config[CONF_TYPE] == "armed_vacation":
        to_state = AlarmControlPanelState.ARMED_VACATION

    state_config = {
        state_trigger.CONF_PLATFORM: "state",
        CONF_ENTITY_ID: config[CONF_ENTITY_ID],
        state_trigger.CONF_TO: to_state,
    }
    if CONF_FOR in config:
        state_config[CONF_FOR] = config[CONF_FOR]
    state_config = await state_trigger.async_validate_trigger_config(hass, state_config)
    return await state_trigger.async_attach_trigger(
        hass, state_config, action, trigger_info, platform_type="device"
    )