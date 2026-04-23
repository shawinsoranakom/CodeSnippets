def _compile_hourly_statistics(session: Session, start: datetime) -> None:
    """Compile hourly statistics.

    This will summarize 5-minute statistics for one hour:
    - average, min max is computed by a database query
    - sum is taken from the last 5-minute entry during the hour
    """
    start_time = start.replace(minute=0)
    start_time_ts = start_time.timestamp()
    end_time = start_time + Statistics.duration
    end_time_ts = end_time.timestamp()

    # Compute last hour's average, min, max
    summary: dict[int, StatisticDataTimestamp] = {}
    stmt = _compile_hourly_statistics_summary_mean_stmt(start_time_ts, end_time_ts)
    stats = execute_stmt_lambda_element(session, stmt)

    if stats:
        for stat in stats:
            metadata_id, _min, _max, _mean, _mean_weight, _mean_type = stat
            if (
                try_parse_enum(StatisticMeanType, _mean_type)
                is StatisticMeanType.CIRCULAR
            ):
                # Normalize the circular mean to be in the range [0, 360)
                _mean = _mean % 360
            summary[metadata_id] = {
                "start_ts": start_time_ts,
                "mean": _mean,
                "mean_weight": _mean_weight,
                "min": _min,
                "max": _max,
            }

    stmt = _compile_hourly_statistics_last_sum_stmt(start_time_ts, end_time_ts)
    # Get last hour's last sum
    stats = execute_stmt_lambda_element(session, stmt)

    if stats:
        for stat in stats:
            metadata_id, start, last_reset_ts, state, _sum, _ = stat
            if metadata_id in summary:
                summary[metadata_id].update(
                    {
                        "last_reset_ts": last_reset_ts,
                        "state": state,
                        "sum": _sum,
                    }
                )
            else:
                summary[metadata_id] = {
                    "start_ts": start_time_ts,
                    "last_reset_ts": last_reset_ts,
                    "state": state,
                    "sum": _sum,
                }

    # Insert compiled hourly statistics in the database
    now_timestamp = time_time()
    session.add_all(
        Statistics.from_stats_ts(metadata_id, summary_item, now_timestamp)
        for metadata_id, summary_item in summary.items()
    )