def _purge_filtered_events(
    instance: Recorder,
    session: Session,
    excluded_event_type_ids: list[int],
    purge_before_timestamp: float,
) -> bool:
    """Remove filtered events and linked states.

    Return true if all events are purged.
    """
    database_engine = instance.database_engine
    assert database_engine is not None
    to_purge = list(
        session.query(Events.event_id, Events.data_id)
        .filter(Events.event_type_id.in_(excluded_event_type_ids))
        .filter(Events.time_fired_ts < purge_before_timestamp)
        .limit(instance.max_bind_vars)
        .all()
    )
    if not to_purge:
        return True
    event_ids, data_ids = zip(*to_purge, strict=False)
    event_ids_set = set(event_ids)
    _LOGGER.debug(
        "Selected %s event_ids to remove that should be filtered", len(event_ids_set)
    )
    if (
        instance.use_legacy_events_index
        and (
            states := session.query(States.state_id)
            .filter(States.event_id.in_(event_ids_set))
            .all()
        )
        and (state_ids := {state_id for (state_id,) in states})
    ):
        # These are legacy states that are linked to an event that are no longer
        # created but since we did not remove them when we stopped adding new ones
        # we will need to purge them here.
        _purge_state_ids(instance, session, state_ids)
    _purge_event_ids(session, event_ids_set)
    if unused_data_ids_set := _select_unused_event_data_ids(
        instance, session, set(data_ids), database_engine
    ):
        _purge_batch_data_ids(instance, session, unused_data_ids_set)
    return False