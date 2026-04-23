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

    has_time = cur_state.attributes.get(CONF_HAS_TIME)
    has_date = cur_state.attributes.get(CONF_HAS_DATE)

    if not (
        (is_valid_datetime(state.state) and has_date and has_time)
        or (is_valid_date(state.state) and has_date and not has_time)
        or (is_valid_time(state.state) and has_time and not has_date)
    ):
        _LOGGER.warning(
            "Invalid state specified for %s: %s", state.entity_id, state.state
        )
        return

    # Return if we are already at the right state.
    if cur_state.state == state.state:
        return

    service_data = {ATTR_ENTITY_ID: state.entity_id}

    if has_time and has_date:
        service_data[ATTR_DATETIME] = state.state
    elif has_time:
        service_data[ATTR_TIME] = state.state
    elif has_date:
        service_data[ATTR_DATE] = state.state

    await hass.services.async_call(
        DOMAIN, "set_datetime", service_data, context=context, blocking=True
    )