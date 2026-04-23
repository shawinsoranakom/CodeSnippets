def get_entity_state_dict(config: Config, entity: State) -> dict[str, Any]:
    """Retrieve and convert state and brightness values for an entity."""
    cached_state_entry = config.cached_states.get(entity.entity_id, None)
    cached_state = None

    # Check if we have a cached entry, and if so if it hasn't expired.
    if cached_state_entry is not None:
        entry_state, entry_time = cached_state_entry
        if entry_time is None:
            # Handle the case where the entity is listed in config.off_maps_to_on_domains.
            cached_state = entry_state
        elif time.time() - entry_time < STATE_CACHED_TIMEOUT and entry_state[
            STATE_ON
        ] == _hass_to_hue_state(entity):
            # We only want to use the cache if the actual state of the entity
            # is in sync so that it can be detected as an error by Alexa.
            cached_state = entry_state
        else:
            # Remove the now stale cached entry.
            config.cached_states.pop(entity.entity_id)

    if cached_state is None:
        return _build_entity_state_dict(entity)

    data: dict[str, Any] = cached_state
    # Make sure brightness is valid
    if data[STATE_BRIGHTNESS] is None:
        data[STATE_BRIGHTNESS] = HUE_API_STATE_BRI_MAX if data[STATE_ON] else 0

    # Make sure hue/saturation are valid
    if (data[STATE_HUE] is None) or (data[STATE_SATURATION] is None):
        data[STATE_HUE] = 0
        data[STATE_SATURATION] = 0

    # If the light is off, set the color to off
    if data[STATE_BRIGHTNESS] == 0:
        data[STATE_HUE] = 0
        data[STATE_SATURATION] = 0

    _clamp_values(data)
    return data