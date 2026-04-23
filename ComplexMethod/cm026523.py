async def async_attach_trigger(
    hass: HomeAssistant,
    config: ConfigType,
    action: TriggerActionType,
    trigger_info: TriggerInfo,
) -> CALLBACK_TYPE:
    """Attach a trigger."""
    if config[CONF_TYPE] in STATE_TRIGGER_TYPES:
        if config[CONF_TYPE] == "opened":
            to_state = CoverState.OPEN
        elif config[CONF_TYPE] == "closed":
            to_state = CoverState.CLOSED
        elif config[CONF_TYPE] == "opening":
            to_state = CoverState.OPENING
        elif config[CONF_TYPE] == "closing":
            to_state = CoverState.CLOSING

        state_config = {
            CONF_PLATFORM: "state",
            CONF_ENTITY_ID: config[CONF_ENTITY_ID],
            state_trigger.CONF_TO: to_state,
        }
        if CONF_FOR in config:
            state_config[CONF_FOR] = config[CONF_FOR]
        state_config = await state_trigger.async_validate_trigger_config(
            hass, state_config
        )
        return await state_trigger.async_attach_trigger(
            hass, state_config, action, trigger_info, platform_type="device"
        )

    if config[CONF_TYPE] == "position":
        position = "current_position"
    if config[CONF_TYPE] == "tilt_position":
        position = "current_tilt_position"
    min_pos = config.get(CONF_ABOVE, -1)
    max_pos = config.get(CONF_BELOW, 101)
    value_template = f"{{{{ state.attributes.{position} }}}}"

    numeric_state_config = {
        CONF_PLATFORM: "numeric_state",
        CONF_ENTITY_ID: config[CONF_ENTITY_ID],
        CONF_BELOW: max_pos,
        CONF_ABOVE: min_pos,
        CONF_VALUE_TEMPLATE: value_template,
    }
    numeric_state_config = await numeric_state_trigger.async_validate_trigger_config(
        hass, numeric_state_config
    )
    return await numeric_state_trigger.async_attach_trigger(
        hass, numeric_state_config, action, trigger_info, platform_type="device"
    )