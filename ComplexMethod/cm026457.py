async def _create_automation_entities(
    hass: HomeAssistant, automation_configs: list[AutomationEntityConfig]
) -> list[BaseAutomationEntity]:
    """Create automation entities from prepared configuration."""
    entities: list[BaseAutomationEntity] = []

    for automation_config in automation_configs:
        config_block = automation_config.config_block

        automation_id: str | None = config_block.get(CONF_ID)
        name = _automation_name(automation_config)

        if automation_config.validation_status != ValidationStatus.OK:
            entities.append(
                UnavailableAutomationEntity(
                    automation_id,
                    name,
                    automation_config.raw_config,
                    cast(str, automation_config.validation_error),
                    automation_config.validation_status,
                )
            )
            continue

        initial_state: bool | None = config_block.get(CONF_INITIAL_STATE)

        action_script = Script(
            hass,
            config_block[CONF_ACTIONS],
            name,
            DOMAIN,
            running_description="automation actions",
            script_mode=config_block[CONF_MODE],
            max_runs=config_block[CONF_MAX],
            max_exceeded=config_block[CONF_MAX_EXCEEDED],
            logger=LOGGER,
            # We don't pass variables here
            # Automation will already render them to use them in the condition
            # and so will pass them on to the script.
        )

        if CONF_CONDITIONS in config_block:
            condition = await _async_process_if(hass, name, config_block)

            if condition is None:
                continue
        else:
            condition = None

        # Add trigger variables to variables
        variables = None
        if CONF_TRIGGER_VARIABLES in config_block and CONF_VARIABLES in config_block:
            variables = ScriptVariables(
                dict(config_block[CONF_TRIGGER_VARIABLES].as_dict())
            )
            variables.variables.update(config_block[CONF_VARIABLES].as_dict())
        elif CONF_TRIGGER_VARIABLES in config_block:
            variables = config_block[CONF_TRIGGER_VARIABLES]
        elif CONF_VARIABLES in config_block:
            variables = config_block[CONF_VARIABLES]

        entity = AutomationEntity(
            automation_id,
            name,
            config_block[CONF_TRIGGERS],
            condition,
            action_script,
            initial_state,
            variables,
            config_block.get(CONF_TRIGGER_VARIABLES),
            automation_config.raw_config,
            automation_config.raw_blueprint_inputs,
            config_block[CONF_TRACE],
        )
        entities.append(entity)

    return entities