def async_condition_from_config(
    hass: HomeAssistant, config: ConfigType
) -> condition.ConditionCheckerType:
    """Create a function to test a device condition."""
    if config[CONF_TYPE] == CONDITION_TRIGGERED:
        state = AlarmControlPanelState.TRIGGERED
    elif config[CONF_TYPE] == CONDITION_DISARMED:
        state = AlarmControlPanelState.DISARMED
    elif config[CONF_TYPE] == CONDITION_ARMED_HOME:
        state = AlarmControlPanelState.ARMED_HOME
    elif config[CONF_TYPE] == CONDITION_ARMED_AWAY:
        state = AlarmControlPanelState.ARMED_AWAY
    elif config[CONF_TYPE] == CONDITION_ARMED_NIGHT:
        state = AlarmControlPanelState.ARMED_NIGHT
    elif config[CONF_TYPE] == CONDITION_ARMED_VACATION:
        state = AlarmControlPanelState.ARMED_VACATION
    elif config[CONF_TYPE] == CONDITION_ARMED_CUSTOM_BYPASS:
        state = AlarmControlPanelState.ARMED_CUSTOM_BYPASS

    registry = er.async_get(hass)
    entity_id = er.async_resolve_entity_id(registry, config[ATTR_ENTITY_ID])

    def test_is_state(hass: HomeAssistant, variables: TemplateVarsType) -> bool:
        """Test if an entity is a certain state."""
        return condition.state(hass, entity_id, state)

    return test_is_state