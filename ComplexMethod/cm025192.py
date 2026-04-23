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

    if state.state not in VALID_STATES:
        _LOGGER.warning(
            "Invalid state specified for %s: %s", state.entity_id, state.state
        )
        return

    # Return if we are already at the right state.
    if (
        cur_state.state == state.state
        and cur_state.attributes.get(ATTR_TEMPERATURE)
        == state.attributes.get(ATTR_TEMPERATURE)
        and cur_state.attributes.get(ATTR_AWAY_MODE)
        == state.attributes.get(ATTR_AWAY_MODE)
    ):
        return

    service_data = {ATTR_ENTITY_ID: state.entity_id}

    if state.state != cur_state.state:
        if state.state == STATE_ON:
            service = SERVICE_TURN_ON
        elif state.state == STATE_OFF:
            service = SERVICE_TURN_OFF
        else:
            service = SERVICE_SET_OPERATION_MODE
            service_data[ATTR_OPERATION_MODE] = state.state

        await hass.services.async_call(
            DOMAIN, service, service_data, context=context, blocking=True
        )

    if (
        state.attributes.get(ATTR_TEMPERATURE)
        != cur_state.attributes.get(ATTR_TEMPERATURE)
        and state.attributes.get(ATTR_TEMPERATURE) is not None
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {
                ATTR_ENTITY_ID: state.entity_id,
                ATTR_TEMPERATURE: state.attributes.get(ATTR_TEMPERATURE),
            },
            context=context,
            blocking=True,
        )

    if (
        state.attributes.get(ATTR_AWAY_MODE) != cur_state.attributes.get(ATTR_AWAY_MODE)
        and state.attributes.get(ATTR_AWAY_MODE) is not None
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_AWAY_MODE,
            {
                ATTR_ENTITY_ID: state.entity_id,
                ATTR_AWAY_MODE: state.attributes.get(ATTR_AWAY_MODE),
            },
            context=context,
            blocking=True,
        )