def async_condition_from_config(
    hass: HomeAssistant, config: ConfigType
) -> condition.ConditionCheckerType:
    """Create a function to test a device condition."""
    registry = er.async_get(hass)
    entity_id = er.async_resolve_entity_id(registry, config[CONF_ENTITY_ID])

    if config[CONF_TYPE] in STATE_CONDITION_TYPES:
        if config[CONF_TYPE] == "is_open":
            state = CoverState.OPEN
        elif config[CONF_TYPE] == "is_closed":
            state = CoverState.CLOSED
        elif config[CONF_TYPE] == "is_opening":
            state = CoverState.OPENING
        elif config[CONF_TYPE] == "is_closing":
            state = CoverState.CLOSING

        def test_is_state(hass: HomeAssistant, variables: TemplateVarsType) -> bool:
            """Test if an entity is a certain state."""
            return condition.state(hass, entity_id, state)

        return test_is_state

    if config[CONF_TYPE] == "is_position":
        position_attr = "current_position"
    if config[CONF_TYPE] == "is_tilt_position":
        position_attr = "current_tilt_position"
    min_pos = config.get(CONF_ABOVE)
    max_pos = config.get(CONF_BELOW)

    @callback
    def check_numeric_state(
        hass: HomeAssistant, variables: TemplateVarsType = None
    ) -> bool:
        """Return whether the criteria are met."""
        return condition.async_numeric_state(
            hass, entity_id, max_pos, min_pos, attribute=position_attr
        )

    return check_numeric_state