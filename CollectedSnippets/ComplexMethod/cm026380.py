async def async_attach_trigger(
    hass: HomeAssistant,
    config: ConfigType,
    action: TriggerActionType,
    trigger_info: TriggerInfo,
) -> CALLBACK_TYPE:
    """Attach a trigger."""
    if (trigger_type := config[CONF_TYPE]) == "hvac_mode_changed":
        state_config = {
            state_trigger.CONF_PLATFORM: "state",
            state_trigger.CONF_ENTITY_ID: config[CONF_ENTITY_ID],
            state_trigger.CONF_TO: config[state_trigger.CONF_TO],
            state_trigger.CONF_FROM: [
                mode
                for mode in const.HVAC_MODES
                if mode != config[state_trigger.CONF_TO]
            ],
        }
        if CONF_FOR in config:
            state_config[CONF_FOR] = config[CONF_FOR]
        state_config = await state_trigger.async_validate_trigger_config(
            hass, state_config
        )
        return await state_trigger.async_attach_trigger(
            hass, state_config, action, trigger_info, platform_type="device"
        )

    numeric_state_config = {
        numeric_state_trigger.CONF_PLATFORM: "numeric_state",
        numeric_state_trigger.CONF_ENTITY_ID: config[CONF_ENTITY_ID],
    }

    if trigger_type == "current_temperature_changed":
        numeric_state_config[numeric_state_trigger.CONF_VALUE_TEMPLATE] = (
            "{{ state.attributes.current_temperature }}"
        )
    else:  # trigger_type == "current_humidity_changed"
        numeric_state_config[numeric_state_trigger.CONF_VALUE_TEMPLATE] = (
            "{{ state.attributes.current_humidity }}"
        )

    if CONF_ABOVE in config:
        numeric_state_config[CONF_ABOVE] = config[CONF_ABOVE]
    if CONF_BELOW in config:
        numeric_state_config[CONF_BELOW] = config[CONF_BELOW]
    if CONF_FOR in config:
        numeric_state_config[CONF_FOR] = config[CONF_FOR]

    numeric_state_config = await numeric_state_trigger.async_validate_trigger_config(
        hass, numeric_state_config
    )
    return await numeric_state_trigger.async_attach_trigger(
        hass, numeric_state_config, action, trigger_info, platform_type="device"
    )