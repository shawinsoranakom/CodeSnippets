def _get_max_mean_min_statistic_in_sub_period(
    session: Session,
    result: _MaxMinMeanStatisticSubPeriod,
    start_time: datetime | None,
    end_time: datetime | None,
    table: type[StatisticsBase],
    types: set[Literal["max", "mean", "min", "change"]],
    metadata: tuple[int, StatisticMetaData],
) -> None:
    """Return max, mean and min during the period."""
    # Calculate max, mean, min
    mean_type = metadata[1]["mean_type"]
    columns = select()
    if "max" in types:
        columns = columns.add_columns(func.max(table.max))
    if "mean" in types:
        match mean_type:
            case StatisticMeanType.ARITHMETIC:
                columns = columns.add_columns(func.avg(table.mean))
                columns = columns.add_columns(func.count(table.mean))
            case StatisticMeanType.CIRCULAR:
                columns = columns.add_columns(*query_circular_mean(table))
    if "min" in types:
        columns = columns.add_columns(func.min(table.min))

    stmt = _generate_max_mean_min_statistic_in_sub_period_stmt(
        columns, start_time, end_time, table, metadata[0]
    )
    stats = cast(Sequence[Row[Any]], execute_stmt_lambda_element(session, stmt))
    if not stats:
        return
    if "max" in types and (new_max := stats[0].max) is not None:
        old_max = result.get("max")
        result["max"] = max(new_max, old_max) if old_max is not None else new_max
    if "mean" in types:
        # https://github.com/sqlalchemy/sqlalchemy/issues/9127
        match mean_type:
            case StatisticMeanType.ARITHMETIC:
                duration = stats[0].count * table.duration.total_seconds()  # type: ignore[operator]
                if stats[0].avg is not None:
                    result["duration"] = result.get("duration", 0.0) + duration
                    result["mean_acc"] = (
                        result.get("mean_acc", 0.0) + stats[0].avg * duration
                    )
            case StatisticMeanType.CIRCULAR:
                if (new_circular_mean := stats[0].mean) is not None and (
                    weight := stats[0].mean_weight
                ) is not None:
                    result["circular_means"].append((new_circular_mean, weight))
    if "min" in types and (new_min := stats[0].min) is not None:
        old_min = result.get("min")
        result["min"] = min(new_min, old_min) if old_min is not None else new_min