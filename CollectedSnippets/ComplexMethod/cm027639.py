async def async_validate_action_config(
    hass: HomeAssistant, config: ConfigType
) -> ConfigType:
    """Validate config."""
    action_type = cv.determine_script_action(config)

    if action_type in STATIC_VALIDATION_ACTION_TYPES:
        pass

    elif action_type == cv.SCRIPT_ACTION_DEVICE_AUTOMATION:
        config = await device_action.async_validate_action_config(hass, config)

    elif action_type == cv.SCRIPT_ACTION_CHECK_CONDITION:
        config = await condition.async_validate_condition_config(hass, config)

    elif action_type == cv.SCRIPT_ACTION_WAIT_FOR_TRIGGER:
        config[
            CONF_WAIT_FOR_TRIGGER
        ] = await trigger_helper.async_validate_trigger_config(
            hass, config[CONF_WAIT_FOR_TRIGGER]
        )

    elif action_type == cv.SCRIPT_ACTION_REPEAT:
        if CONF_UNTIL in config[CONF_REPEAT]:
            conditions = await condition.async_validate_conditions_config(
                hass, config[CONF_REPEAT][CONF_UNTIL]
            )
            config[CONF_REPEAT][CONF_UNTIL] = conditions
        if CONF_WHILE in config[CONF_REPEAT]:
            conditions = await condition.async_validate_conditions_config(
                hass, config[CONF_REPEAT][CONF_WHILE]
            )
            config[CONF_REPEAT][CONF_WHILE] = conditions
        config[CONF_REPEAT][CONF_SEQUENCE] = await async_validate_actions_config(
            hass, config[CONF_REPEAT][CONF_SEQUENCE]
        )

    elif action_type == cv.SCRIPT_ACTION_CHOOSE:
        if CONF_DEFAULT in config:
            config[CONF_DEFAULT] = await async_validate_actions_config(
                hass, config[CONF_DEFAULT]
            )

        for choose_conf in config[CONF_CHOOSE]:
            conditions = await condition.async_validate_conditions_config(
                hass, choose_conf[CONF_CONDITIONS]
            )
            choose_conf[CONF_CONDITIONS] = conditions
            choose_conf[CONF_SEQUENCE] = await async_validate_actions_config(
                hass, choose_conf[CONF_SEQUENCE]
            )

    elif action_type == cv.SCRIPT_ACTION_IF:
        config[CONF_IF] = await condition.async_validate_conditions_config(
            hass, config[CONF_IF]
        )
        config[CONF_THEN] = await async_validate_actions_config(hass, config[CONF_THEN])
        if CONF_ELSE in config:
            config[CONF_ELSE] = await async_validate_actions_config(
                hass, config[CONF_ELSE]
            )

    elif action_type == cv.SCRIPT_ACTION_PARALLEL:
        for parallel_conf in config[CONF_PARALLEL]:
            parallel_conf[CONF_SEQUENCE] = await async_validate_actions_config(
                hass, parallel_conf[CONF_SEQUENCE]
            )

    elif action_type == cv.SCRIPT_ACTION_SEQUENCE:
        config[CONF_SEQUENCE] = await async_validate_actions_config(
            hass, config[CONF_SEQUENCE]
        )

    else:
        raise ValueError(f"No validation for {action_type}")

    return config