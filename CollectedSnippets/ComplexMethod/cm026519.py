async def _async_reproduce_state(
    hass: HomeAssistant,
    state: State,
    *,
    context: Context | None = None,
    reproduce_options: dict[str, Any] | None = None,
) -> None:
    """Reproduce a single state."""
    entity_id = state.entity_id
    if (cur_state := hass.states.get(entity_id)) is None:
        _LOGGER.warning("Unable to find entity %s", entity_id)
        return

    if (target_state := state.state) not in VALID_STATES:
        _LOGGER.warning("Invalid state specified for %s: %s", entity_id, target_state)
        return

    current_attrs = cur_state.attributes
    target_attrs = state.attributes

    current_position: int | None = current_attrs.get(ATTR_CURRENT_POSITION)
    target_position: int | None = target_attrs.get(ATTR_CURRENT_POSITION)
    position_matches = current_position == target_position

    current_tilt_position: int | None = current_attrs.get(ATTR_CURRENT_TILT_POSITION)
    target_tilt_position: int | None = target_attrs.get(ATTR_CURRENT_TILT_POSITION)
    tilt_position_matches = current_tilt_position == target_tilt_position

    state_matches = cur_state.state == target_state
    # Return if we are already at the right state.
    if state_matches and position_matches and tilt_position_matches:
        return

    features = try_parse_enum(
        CoverEntityFeature, current_attrs.get(ATTR_SUPPORTED_FEATURES)
    )
    if features is None:
        # Backwards compatibility for integrations that
        # don't set supported features since it previously
        # worked without it.
        _LOGGER.warning("Supported features is not set for %s", entity_id)
        features = _determine_features(current_attrs)

    service_call = partial(
        hass.services.async_call,
        DOMAIN,
        context=context,
        blocking=True,
    )
    service_data = {ATTR_ENTITY_ID: entity_id}

    set_position = target_position is not None and await _async_set_position(
        service_call, service_data, features, target_position
    )
    set_tilt = target_tilt_position is not None and await _async_set_tilt_position(
        service_call, service_data, features, target_tilt_position
    )

    if target_state in CLOSING_STATES:
        await _async_close_cover(
            service_call, service_data, features, set_position, set_tilt
        )

    elif target_state in OPENING_STATES:
        await _async_open_cover(
            service_call, service_data, features, set_position, set_tilt
        )