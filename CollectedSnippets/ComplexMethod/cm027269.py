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

    if not state.state.isdigit():
        _LOGGER.warning(
            "Invalid state specified for %s: %s", state.entity_id, state.state
        )
        return

    # Return if we are already at the right state.
    if (
        cur_state.state == state.state
        and cur_state.attributes.get(ATTR_MAXIMUM) == state.attributes.get(ATTR_MAXIMUM)
        and cur_state.attributes.get(ATTR_MINIMUM) == state.attributes.get(ATTR_MINIMUM)
        and cur_state.attributes.get(ATTR_STEP) == state.attributes.get(ATTR_STEP)
    ):
        return

    service_data = {ATTR_ENTITY_ID: state.entity_id, VALUE: state.state}
    service = SERVICE_SET_VALUE
    if ATTR_MAXIMUM in state.attributes:
        service_data[ATTR_MAXIMUM] = state.attributes[ATTR_MAXIMUM]
    if ATTR_MINIMUM in state.attributes:
        service_data[ATTR_MINIMUM] = state.attributes[ATTR_MINIMUM]
    if ATTR_STEP in state.attributes:
        service_data[ATTR_STEP] = state.attributes[ATTR_STEP]

    await hass.services.async_call(
        DOMAIN, service, service_data, context=context, blocking=True
    )