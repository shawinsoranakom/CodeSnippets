def purge_old_data(
    instance: Recorder,
    purge_before: datetime,
    repack: bool,
    apply_filter: bool = False,
    events_batch_size: int = DEFAULT_EVENTS_BATCHES_PER_PURGE,
    states_batch_size: int = DEFAULT_STATES_BATCHES_PER_PURGE,
) -> bool:
    """Purge events and states older than purge_before.

    Cleans up an timeframe of an hour, based on the oldest record.
    """
    _LOGGER.debug(
        "Purging states and events before target %s",
        purge_before.isoformat(sep=" ", timespec="seconds"),
    )
    with session_scope(session=instance.get_session()) as session:
        # Purge a max of max_bind_vars, based on the oldest states or events record
        has_more_to_purge = False
        if instance.use_legacy_events_index and _purging_legacy_format(session):
            _LOGGER.debug(
                "Purge running in legacy format as there are states with event_id"
                " remaining"
            )
            has_more_to_purge |= _purge_legacy_format(instance, session, purge_before)
        else:
            _LOGGER.debug(
                "Purge running in new format as there are NO states with event_id"
                " remaining"
            )
            # Once we are done purging legacy rows, we use the new method
            has_more_to_purge |= _purge_states_and_attributes_ids(
                instance, session, states_batch_size, purge_before
            )
            has_more_to_purge |= _purge_events_and_data_ids(
                instance, session, events_batch_size, purge_before
            )

        statistics_runs = _select_statistics_runs_to_purge(
            session, purge_before, instance.max_bind_vars
        )
        short_term_statistics = _select_short_term_statistics_to_purge(
            session, purge_before, instance.max_bind_vars
        )
        if statistics_runs:
            _purge_statistics_runs(session, statistics_runs)

        if short_term_statistics:
            _purge_short_term_statistics(session, short_term_statistics)

        if has_more_to_purge or statistics_runs or short_term_statistics:
            # Return false, as we might not be done yet.
            _LOGGER.debug("Purging hasn't fully completed yet")
            return False

        if apply_filter and not _purge_filtered_data(instance, session):
            _LOGGER.debug("Cleanup filtered data hasn't fully completed yet")
            return False

        # This purge cycle is finished, clean up old event types and
        # recorder runs
        _purge_old_event_types(instance, session)
        _purge_old_entity_ids(instance, session)

        _purge_old_recorder_runs(instance, session, purge_before)
    with session_scope(session=instance.get_session(), read_only=True) as session:
        instance.recorder_runs_manager.load_from_db(session)
        instance.states_manager.load_from_db(session)
    if repack:
        repack_database(instance)
    return True