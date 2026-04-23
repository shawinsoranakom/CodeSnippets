def _get_oldest_sum_statistic(
    session: Session,
    head_start_time: datetime | None,
    main_start_time: datetime | None,
    tail_start_time: datetime | None,
    oldest_stat: datetime | None,
    oldest_5_min_stat: datetime | None,
    tail_only: bool,
    metadata_id: int,
) -> float | None:
    """Return the oldest non-NULL sum during the period."""

    def _get_oldest_sum_statistic_in_sub_period(
        session: Session,
        start_time: datetime | None,
        table: type[StatisticsBase],
        metadata_id: int,
    ) -> float | None:
        """Return the oldest non-NULL sum during the period."""
        stmt = lambda_stmt(
            lambda: (
                select(table.sum)
                .filter(table.metadata_id == metadata_id)
                .filter(table.sum.is_not(None))
                .order_by(table.start_ts.asc())
                .limit(1)
            )
        )
        if start_time is not None:
            start_time = start_time + table.duration - timedelta.resolution
            if table == StatisticsShortTerm:
                minutes = start_time.minute - start_time.minute % 5
                period = start_time.replace(minute=minutes, second=0, microsecond=0)
            else:
                period = start_time.replace(minute=0, second=0, microsecond=0)
            prev_period = period - table.duration
            prev_period_ts = prev_period.timestamp()
            stmt += lambda q: q.filter(table.start_ts >= prev_period_ts)
        stats = cast(Sequence[Row], execute_stmt_lambda_element(session, stmt))
        return stats[0].sum if stats else None

    oldest_sum: float | None = None

    # This function won't be called if tail_only is False and main_start_time is None
    # the extra checks are added to satisfy MyPy
    if not tail_only and main_start_time is not None and oldest_stat is not None:
        period = main_start_time.replace(minute=0, second=0, microsecond=0)
        prev_period = period - Statistics.duration
        if prev_period < oldest_stat:
            return 0

    if (
        head_start_time is not None
        and oldest_5_min_stat is not None
        and (
            # If we want stats older than the short term purge window, don't lookup
            # the oldest sum in the short term table, as it would be prioritized
            # over older LongTermStats.
            (oldest_stat is None)
            or (oldest_5_min_stat < oldest_stat)
            or (oldest_5_min_stat <= head_start_time)
        )
        and (
            oldest_sum := _get_oldest_sum_statistic_in_sub_period(
                session, head_start_time, StatisticsShortTerm, metadata_id
            )
        )
        is not None
    ):
        return oldest_sum

    if not tail_only:
        if (
            oldest_sum := _get_oldest_sum_statistic_in_sub_period(
                session, main_start_time, Statistics, metadata_id
            )
        ) is not None:
            return oldest_sum
        return 0

    if (
        tail_start_time is not None
        and (
            oldest_sum := _get_oldest_sum_statistic_in_sub_period(
                session, tail_start_time, StatisticsShortTerm, metadata_id
            )
        )
    ) is not None:
        return oldest_sum

    return 0