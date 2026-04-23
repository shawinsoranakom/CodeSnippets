async def _async_reproduce_state(
    hass: HomeAssistant,
    state: State,
    *,
    context: Context | None = None,
    reproduce_options: dict[str, Any] | None = None,
) -> None:
    """Reproduce a single state."""
    if (cur_state := hass.states.get(state.entity_id)) is None:
        _LOGGER.warning("Unable to find entity %s", state.entity_id)
        return

    if not (state.state in VALID_STATES_TOGGLE or state.state in VALID_STATES_STATE):
        _LOGGER.warning(
            "Invalid state specified for %s: %s", state.entity_id, state.state
        )
        return

    # Return if we are already at the right state.
    if cur_state.state == state.state and cur_state.attributes.get(
        ATTR_FAN_SPEED
    ) == state.attributes.get(ATTR_FAN_SPEED):
        return

    service_data = {ATTR_ENTITY_ID: state.entity_id}

    if cur_state.state != state.state:
        # Wrong state
        if state.state == STATE_ON:
            service = SERVICE_TURN_ON
        elif state.state == STATE_OFF:
            service = SERVICE_TURN_OFF
        elif state.state == VacuumActivity.CLEANING:
            service = SERVICE_START
        elif state.state in [VacuumActivity.DOCKED, VacuumActivity.RETURNING]:
            service = SERVICE_RETURN_TO_BASE
        elif state.state == VacuumActivity.IDLE:
            service = SERVICE_STOP
        elif state.state == VacuumActivity.PAUSED:
            service = SERVICE_PAUSE

        await hass.services.async_call(
            DOMAIN, service, service_data, context=context, blocking=True
        )

    if cur_state.attributes.get(ATTR_FAN_SPEED) != state.attributes.get(ATTR_FAN_SPEED):
        # Wrong fan speed
        service_data["fan_speed"] = state.attributes[ATTR_FAN_SPEED]
        await hass.services.async_call(
            DOMAIN, SERVICE_SET_FAN_SPEED, service_data, context=context, blocking=True
        )