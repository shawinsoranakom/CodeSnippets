def _reduce_statistics(
    stats: dict[str, list[StatisticsRow]],
    same_period: Callable[[float, float], bool],
    period_start_end: Callable[[float], tuple[float, float]],
    period: timedelta,
    types: set[Literal["last_reset", "max", "mean", "min", "state", "sum"]],
    metadata: dict[str, tuple[int, StatisticMetaData]],
) -> dict[str, list[StatisticsRow]]:
    """Reduce hourly statistics to daily or monthly statistics."""
    result: dict[str, list[StatisticsRow]] = defaultdict(list)
    period_seconds = period.total_seconds()
    _want_mean = "mean" in types
    _want_min = "min" in types
    _want_max = "max" in types
    _want_last_reset = "last_reset" in types
    _want_state = "state" in types
    _want_sum = "sum" in types
    for statistic_id, stat_list in stats.items():
        max_values: list[float] = []
        mean_values: list[tuple[float, float]] = []
        min_values: list[float] = []
        prev_stat: StatisticsRow = stat_list[0]
        fake_entry: StatisticsRow = {"start": stat_list[-1]["start"] + period_seconds}

        # Loop over the hourly statistics + a fake entry to end the period
        for statistic in chain(stat_list, (fake_entry,)):
            if not same_period(prev_stat["start"], statistic["start"]):
                start, end = period_start_end(prev_stat["start"])
                # The previous statistic was the last entry of the period
                row: StatisticsRow = {
                    "start": start,
                    "end": end,
                }
                if _want_mean:
                    row["mean"] = None
                    row["mean_weight"] = None
                    if mean_values:
                        match metadata[statistic_id][1]["mean_type"]:
                            case StatisticMeanType.ARITHMETIC:
                                row["mean"] = mean([x[0] for x in mean_values])
                            case StatisticMeanType.CIRCULAR:
                                row["mean"], row["mean_weight"] = (
                                    weighted_circular_mean(mean_values)
                                )
                    mean_values.clear()
                if _want_min:
                    row["min"] = min(min_values) if min_values else None
                    min_values.clear()
                if _want_max:
                    row["max"] = max(max_values) if max_values else None
                    max_values.clear()
                if _want_last_reset:
                    row["last_reset"] = prev_stat.get("last_reset")
                if _want_state:
                    row["state"] = prev_stat.get("state")
                if _want_sum:
                    row["sum"] = prev_stat["sum"]
                result[statistic_id].append(row)
            if _want_max and (_max := statistic.get("max")) is not None:
                max_values.append(_max)
            if _want_mean:
                if (_mean := statistic.get("mean")) is not None:
                    _mean_weight = statistic.get("mean_weight") or 0.0
                    mean_values.append((_mean, _mean_weight))
            if _want_min and (_min := statistic.get("min")) is not None:
                min_values.append(_min)
            prev_stat = statistic

    return result