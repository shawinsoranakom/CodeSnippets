def _get_max_mean_min_statistic(
    session: Session,
    head_start_time: datetime | None,
    head_end_time: datetime | None,
    main_start_time: datetime | None,
    main_end_time: datetime | None,
    tail_start_time: datetime | None,
    tail_end_time: datetime | None,
    tail_only: bool,
    metadata: tuple[int, StatisticMetaData],
    types: set[Literal["max", "mean", "min", "change"]],
) -> dict[str, float | None]:
    """Return max, mean and min during the period.

    The mean is time weighted, combining hourly and 5-minute statistics if
    necessary.
    """
    max_mean_min = _MaxMinMeanStatisticSubPeriod(circular_means=[])
    result: dict[str, float | None] = {}

    if tail_start_time is not None:
        # Calculate max, mean, min
        _get_max_mean_min_statistic_in_sub_period(
            session,
            max_mean_min,
            tail_start_time,
            tail_end_time,
            StatisticsShortTerm,
            types,
            metadata,
        )

    if not tail_only:
        _get_max_mean_min_statistic_in_sub_period(
            session,
            max_mean_min,
            main_start_time,
            main_end_time,
            Statistics,
            types,
            metadata,
        )

    if head_start_time is not None:
        _get_max_mean_min_statistic_in_sub_period(
            session,
            max_mean_min,
            head_start_time,
            head_end_time,
            StatisticsShortTerm,
            types,
            metadata,
        )

    if "max" in types:
        result["max"] = max_mean_min.get("max")
    if "mean" in types:
        mean_value = None
        match metadata[1]["mean_type"]:
            case StatisticMeanType.CIRCULAR:
                if circular_means := max_mean_min["circular_means"]:
                    mean_value = weighted_circular_mean(circular_means)[0]
            case StatisticMeanType.ARITHMETIC:
                if (mean_value := max_mean_min.get("mean_acc")) is not None and (
                    duration := max_mean_min.get("duration")
                ) is not None:
                    mean_value = mean_value / duration
        result["mean"] = mean_value
    if "min" in types:
        result["min"] = max_mean_min.get("min")
    return result