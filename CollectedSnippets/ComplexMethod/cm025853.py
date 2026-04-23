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
        and _color_mode_same(cur_state, state)
        and all(
            check_attr_equal(cur_state.attributes, state.attributes, attr)
            for attr in ATTR_GROUP + COLOR_GROUP
        )
    ):
        return

    service_data: dict[str, Any] = {ATTR_ENTITY_ID: state.entity_id}

    if reproduce_options is not None and ATTR_TRANSITION in reproduce_options:
        service_data[ATTR_TRANSITION] = reproduce_options[ATTR_TRANSITION]

    if state.state == STATE_ON:
        service = SERVICE_TURN_ON
        for attr in ATTR_GROUP:
            # All attributes that are not colors
            if (attr_state := state.attributes.get(attr)) is not None:
                service_data[attr] = attr_state

        if (
            state.attributes.get(ATTR_COLOR_MODE, ColorMode.UNKNOWN)
            != ColorMode.UNKNOWN
        ):
            color_mode = state.attributes[ATTR_COLOR_MODE]
            if cm_attr := COLOR_MODE_TO_ATTRIBUTE.get(color_mode):
                if (cm_attr_state := state.attributes.get(cm_attr.state_attr)) is None:
                    _LOGGER.warning(
                        "Color mode %s specified but attribute %s missing for: %s",
                        color_mode,
                        cm_attr.state_attr,
                        state.entity_id,
                    )
                    return
                service_data[cm_attr.parameter] = cm_attr_state
        else:
            # Fall back to Choosing the first color that is specified
            for color_attr in COLOR_GROUP:
                if (color_attr_state := state.attributes.get(color_attr)) is not None:
                    service_data[color_attr] = color_attr_state
                    break

    elif state.state == STATE_OFF:
        service = SERVICE_TURN_OFF

    await hass.services.async_call(
        DOMAIN, service, service_data, context=context, blocking=True
    )