def _compile_statistics(
    instance: Recorder, session: Session, start: datetime, fire_events: bool
) -> set[str]:
    """Compile 5-minute statistics for all integrations with a recorder platform.

    This is a helper function for compile_statistics and compile_missing_statistics
    that does not retry on database errors since both callers already retry.

    returns a set of modified statistic_ids if any were modified.
    """
    assert start.tzinfo == dt_util.UTC, "start must be in UTC"
    end = start + StatisticsShortTerm.duration
    statistics_meta_manager = instance.statistics_meta_manager
    modified_statistic_ids: set[str] = set()

    # Return if we already have 5-minute statistics for the requested period
    if execute_stmt_lambda_element(session, _get_first_id_stmt(start)):
        _LOGGER.debug("Statistics already compiled for %s-%s", start, end)
        return modified_statistic_ids

    _LOGGER.debug("Compiling statistics for %s-%s", start, end)
    platform_stats: list[StatisticResult] = []
    current_metadata: dict[str, tuple[int, StatisticMetaData]] = {}
    custom_equivalent_units_per_entity = _get_custom_equivalent_units(instance.hass)
    # Collect statistics from all platforms implementing support
    for domain, platform in instance.hass.data[
        DATA_RECORDER
    ].recorder_platforms.items():
        if not (
            platform_compile_statistics := getattr(
                platform, INTEGRATION_PLATFORM_COMPILE_STATISTICS, None
            )
        ):
            continue
        compiled: PlatformCompiledStatistics = platform_compile_statistics(
            instance.hass, session, start, end, custom_equivalent_units_per_entity
        )
        _LOGGER.debug(
            "Statistics for %s during %s-%s: %s",
            domain,
            start,
            end,
            compiled.platform_stats,
        )
        platform_stats.extend(compiled.platform_stats)
        current_metadata.update(compiled.current_metadata)

    new_short_term_stats: list[StatisticsBase] = []
    updated_metadata_ids: set[int] = set()
    now_timestamp = time_time()
    # Insert collected statistics in the database
    for stats in platform_stats:
        modified_statistic_id, metadata_id = statistics_meta_manager.update_or_add(
            session, stats["meta"], current_metadata
        )
        if modified_statistic_id is not None:
            modified_statistic_ids.add(modified_statistic_id)
        updated_metadata_ids.add(metadata_id)
        if new_stat := _insert_statistics(
            session, StatisticsShortTerm, metadata_id, stats["stat"], now_timestamp
        ):
            new_short_term_stats.append(new_stat)

    if start.minute == 50:
        # Once every hour, update issues
        for platform in instance.hass.data[DATA_RECORDER].recorder_platforms.values():
            if not (
                platform_update_issues := getattr(
                    platform, INTEGRATION_PLATFORM_UPDATE_STATISTICS_ISSUES, None
                )
            ):
                continue
            platform_update_issues(
                instance.hass, session, custom_equivalent_units_per_entity
            )

    if start.minute == 55:
        # A full hour is ready, summarize it
        _compile_hourly_statistics(session, start)

    session.add(StatisticsRuns(start=start))

    if fire_events:
        instance.hass.bus.fire(EVENT_RECORDER_5MIN_STATISTICS_GENERATED)
        if start.minute == 55:
            instance.hass.bus.fire(EVENT_RECORDER_HOURLY_STATISTICS_GENERATED)

    if updated_metadata_ids:
        # These are always the newest statistics, so we can update
        # the run cache without having to check the start_ts.
        session.flush()  # populate the ids of the new StatisticsShortTerm rows
        run_cache = get_short_term_statistics_run_cache(instance.hass)
        # metadata_id is typed to allow None, but we know it's not None here
        # so we can safely cast it to int.
        run_cache.set_latest_ids_for_metadata_ids(
            cast(
                dict[int, int],
                {
                    new_stat.metadata_id: new_stat.id
                    for new_stat in new_short_term_stats
                },
            )
        )

    return modified_statistic_ids