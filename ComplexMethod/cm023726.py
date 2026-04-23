def db_state_to_native(state: States, validate_entity_id: bool = True) -> State | None:
    """Convert to an HA state object."""
    context = ha.Context(
        id=bytes_to_ulid_or_none(state.context_id_bin),
        user_id=bytes_to_uuid_hex_or_none(state.context_user_id_bin),
        parent_id=bytes_to_ulid_or_none(state.context_parent_id_bin),
    )
    attrs = json_loads_object(state.attributes) if state.attributes else {}
    last_updated = dt_util.utc_from_timestamp(state.last_updated_ts or 0)
    if state.last_changed_ts is None or state.last_changed_ts == state.last_updated_ts:
        last_changed = dt_util.utc_from_timestamp(state.last_updated_ts or 0)
    else:
        last_changed = dt_util.utc_from_timestamp(state.last_changed_ts or 0)
    if (
        state.last_reported_ts is None
        or state.last_reported_ts == state.last_updated_ts
    ):
        last_reported = dt_util.utc_from_timestamp(state.last_updated_ts or 0)
    else:
        last_reported = dt_util.utc_from_timestamp(state.last_reported_ts or 0)
    return State(
        state.entity_id or "",
        state.state,  # type: ignore[arg-type]
        # Join the state_attributes table on attributes_id to get the attributes
        # for newer states
        attrs,
        last_changed=last_changed,
        last_reported=last_reported,
        last_updated=last_updated,
        context=context,
        validate_entity_id=validate_entity_id,
    )