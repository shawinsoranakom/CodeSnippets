def _purge_filtered_data(instance: Recorder, session: Session) -> bool:
    """Remove filtered states and events that shouldn't be in the database.

    Returns true if all states and events are purged.
    """
    _LOGGER.debug("Cleanup filtered data")
    database_engine = instance.database_engine
    assert database_engine is not None
    now_timestamp = time.time()

    # Check if excluded entity_ids are in database
    entity_filter = instance.entity_filter
    has_more_to_purge = False
    excluded_metadata_ids: list[str] = [
        metadata_id
        for (metadata_id, entity_id) in session.query(
            StatesMeta.metadata_id, StatesMeta.entity_id
        ).all()
        if entity_filter and not entity_filter(entity_id)
    ]
    if excluded_metadata_ids:
        has_more_to_purge |= not _purge_filtered_states(
            instance, session, excluded_metadata_ids, database_engine, now_timestamp
        )

    # Check if excluded event_types are in database
    if (
        event_type_to_event_type_ids := instance.event_type_manager.get_many(
            instance.exclude_event_types, session
        )
    ) and (
        excluded_event_type_ids := [
            event_type_id
            for event_type_id in event_type_to_event_type_ids.values()
            if event_type_id is not None
        ]
    ):
        has_more_to_purge |= not _purge_filtered_events(
            instance, session, excluded_event_type_ids, now_timestamp
        )

    # Purge has completed if there are not more state or events to purge
    return not has_more_to_purge