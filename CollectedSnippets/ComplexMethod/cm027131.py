def get_latest_short_term_statistics_with_session(
    hass: HomeAssistant,
    session: Session,
    statistic_ids: set[str],
    types: set[Literal["last_reset", "max", "mean", "min", "state", "sum"]],
    metadata: dict[str, tuple[int, StatisticMetaData]] | None = None,
) -> dict[str, list[StatisticsRow]]:
    """Return the latest short term statistics for a list of statistic_ids with a session."""
    # Fetch metadata for the given statistic_ids
    if not metadata:
        metadata = get_instance(hass).statistics_meta_manager.get_many(
            session, statistic_ids=statistic_ids
        )
    if not metadata:
        return {}
    metadata_ids = set(
        _extract_metadata_and_discard_impossible_columns(metadata, types)
    )
    run_cache = get_short_term_statistics_run_cache(hass)
    # Try to find the latest short term statistics ids for the metadata_ids
    # from the run cache first if we have it. If the run cache references
    # a non-existent id because of a purge, we will detect it missing in the
    # next step and run a query to re-populate the cache.
    stats: list[Row] = []
    if metadata_id_to_id := run_cache.get_latest_ids(metadata_ids):
        stats = get_latest_short_term_statistics_by_ids(
            session, metadata_id_to_id.values()
        )
    # If we are missing some metadata_ids in the run cache, we need run a query
    # to populate the cache for each metadata_id, and then run another query
    # to get the latest short term statistics for the missing metadata_ids.
    if (missing_metadata_ids := metadata_ids - set(metadata_id_to_id)) and (
        found_latest_ids := {
            latest_id
            for metadata_id in missing_metadata_ids
            if (
                latest_id := cache_latest_short_term_statistic_id_for_metadata_id(
                    run_cache,
                    session,
                    metadata_id,
                )
            )
            is not None
        }
    ):
        stats.extend(get_latest_short_term_statistics_by_ids(session, found_latest_ids))

    if not stats:
        return {}

    # Return statistics combined with metadata
    return _sorted_statistics_to_dict(
        hass,
        stats,
        statistic_ids,
        metadata,
        False,
        StatisticsShortTerm,
        None,
        types,
    )