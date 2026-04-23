async def async_validate_trigger_config(
    hass: HomeAssistant, config: ConfigType
) -> ConfigType:
    """Validate config."""
    config = TRIGGER_SCHEMA(config)

    # if device is available verify parameters against device capabilities
    trigger = (config[CONF_TYPE], config[CONF_SUBTYPE])

    if config[CONF_TYPE] in RPC_INPUTS_EVENTS_TYPES:
        rpc_coordinator = get_rpc_coordinator_by_device_id(hass, config[CONF_DEVICE_ID])
        if not rpc_coordinator or not rpc_coordinator.device.initialized:
            return config

        input_triggers = get_rpc_input_triggers(rpc_coordinator.device)
        if trigger in input_triggers:
            return config

    elif config[CONF_TYPE] in BLOCK_INPUTS_EVENTS_TYPES:
        block_coordinator = get_block_coordinator_by_device_id(
            hass, config[CONF_DEVICE_ID]
        )
        if not block_coordinator or not block_coordinator.device.initialized:
            return config

        assert block_coordinator.device.blocks

        for block in block_coordinator.device.blocks:
            input_triggers = get_block_input_triggers(block_coordinator.device, block)
            if trigger in input_triggers:
                return config

    raise InvalidDeviceAutomationConfig(
        translation_domain=DOMAIN,
        translation_key="invalid_trigger",
        translation_placeholders={"trigger": str(trigger)},
    )