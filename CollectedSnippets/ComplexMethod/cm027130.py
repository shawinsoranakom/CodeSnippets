def _statistics_during_period_with_session(
    hass: HomeAssistant,
    session: Session,
    start_time: datetime,
    end_time: datetime | None,
    statistic_ids: set[str] | None,
    period: Literal["5minute", "day", "hour", "week", "month", "year"],
    units: dict[str, str] | None,
    _types: set[Literal["change", "last_reset", "max", "mean", "min", "state", "sum"]],
) -> dict[str, list[StatisticsRow]]:
    """Return statistic data points during UTC period start_time - end_time.

    If end_time is omitted, returns statistics newer than or equal to start_time.
    If statistic_ids is omitted, returns statistics for all statistics ids.
    """
    if statistic_ids is not None and not isinstance(statistic_ids, set):
        # This is for backwards compatibility to avoid a breaking change
        # for custom integrations that call this method.
        statistic_ids = set(statistic_ids)  # type: ignore[unreachable]
    # Fetch metadata for the given (or all) statistic_ids
    metadata = get_instance(hass).statistics_meta_manager.get_many(
        session, statistic_ids=statistic_ids
    )
    if not metadata:
        return {}

    types: set[Literal["last_reset", "max", "mean", "min", "state", "sum"]] = set()
    for stat_type in _types:
        if stat_type == "change":
            types.add("sum")
            continue
        types.add(stat_type)

    metadata_ids = None
    if statistic_ids is not None:
        metadata_ids = _extract_metadata_and_discard_impossible_columns(metadata, types)

    # Align start_time and end_time with the period
    if period == "day":
        start_time = dt_util.as_local(start_time).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        start_time = start_time.replace()
        if end_time is not None:
            end_local = dt_util.as_local(end_time)
            end_time = end_local.replace(
                hour=0, minute=0, second=0, microsecond=0
            ) + timedelta(days=1)
    elif period == "week":
        start_local = dt_util.as_local(start_time)
        start_time = start_local.replace(
            hour=0, minute=0, second=0, microsecond=0
        ) - timedelta(days=start_local.weekday())
        if end_time is not None:
            end_local = dt_util.as_local(end_time)
            end_time = (
                end_local.replace(hour=0, minute=0, second=0, microsecond=0)
                - timedelta(days=end_local.weekday())
                + timedelta(days=7)
            )
    elif period == "month":
        start_time = dt_util.as_local(start_time).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        if end_time is not None:
            end_time = _find_month_end_time(dt_util.as_local(end_time))

    elif period == "year":
        start_time = dt_util.as_local(start_time).replace(
            month=1, day=1, hour=0, minute=0, second=0, microsecond=0
        )
        if end_time is not None:
            end_local = dt_util.as_local(end_time)
            end_time = end_local.replace(
                year=end_local.year + 1,
                month=1,
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

    table: type[Statistics | StatisticsShortTerm] = (
        Statistics if period != "5minute" else StatisticsShortTerm
    )
    stmt = _generate_statistics_during_period_stmt(
        start_time, end_time, metadata_ids, table, types
    )
    stats = cast(
        Sequence[Row], execute_stmt_lambda_element(session, stmt, orm_rows=False)
    )

    if not stats:
        return {}

    result = _sorted_statistics_to_dict(
        hass,
        stats,
        statistic_ids,
        metadata,
        True,
        table,
        units,
        types,
    )

    if period == "day":
        result = _reduce_statistics_per_day(result, types, metadata)

    if period == "week":
        result = _reduce_statistics_per_week(result, types, metadata)

    if period == "month":
        result = _reduce_statistics_per_month(result, types, metadata)

    if period == "year":
        result = _reduce_statistics_per_year(result, types, metadata)

    if "change" in _types:
        _augment_result_with_change(
            hass, session, start_time, units, _types, table, metadata, result
        )

    # filter out mean_weight as it is only needed to reduce statistics
    # and not needed in the result
    for stats_rows in result.values():
        for row in stats_rows:
            row.pop("mean_weight", None)

    # Return statistics combined with metadata
    return result