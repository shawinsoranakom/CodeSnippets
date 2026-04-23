def statistic_during_period(
    hass: HomeAssistant,
    start_time: datetime | None,
    end_time: datetime | None,
    statistic_id: str,
    types: set[Literal["max", "mean", "min", "change"]] | None,
    units: dict[str, str] | None,
) -> dict[str, Any]:
    """Return a statistic data point for the UTC period start_time - end_time."""
    metadata = None

    if not types:
        types = {"max", "mean", "min", "change"}

    result: dict[str, Any] = {}

    with session_scope(hass=hass, read_only=True) as session:
        # Fetch metadata for the given statistic_id
        if not (
            metadata := get_instance(hass).statistics_meta_manager.get(
                session, statistic_id
            )
        ):
            return result

        metadata_id = metadata[0]

        oldest_stat = _first_statistic(session, Statistics, metadata_id)
        oldest_5_min_stat = None
        if not valid_statistic_id(statistic_id):
            oldest_5_min_stat = _first_statistic(
                session, StatisticsShortTerm, metadata_id
            )

        # To calculate the summary, data from the statistics (hourly) and
        # short_term_statistics (5 minute) tables is combined
        # - The short term statistics table is used for the head and tail of the period,
        #   if the period it doesn't start or end on a full hour
        # - The statistics table is used for the remainder of the time
        now = dt_util.utcnow()
        if end_time is not None and end_time > now:
            end_time = now

        tail_only = (
            start_time is not None
            and end_time is not None
            and end_time - start_time < Statistics.duration
        )

        # Calculate the head period
        head_start_time: datetime | None = None
        head_end_time: datetime | None = None
        if (
            not tail_only
            and oldest_stat is not None
            and oldest_5_min_stat is not None
            and oldest_5_min_stat - oldest_stat < Statistics.duration
            and (start_time is None or start_time < oldest_5_min_stat)
        ):
            # To improve accuracy of averaged for statistics which were added within
            # recorder's retention period.
            head_start_time = oldest_5_min_stat
            head_end_time = (
                oldest_5_min_stat.replace(minute=0, second=0, microsecond=0)
                + Statistics.duration
            )
        elif not tail_only and start_time is not None and start_time.minute:
            head_start_time = start_time
            head_end_time = (
                start_time.replace(minute=0, second=0, microsecond=0)
                + Statistics.duration
            )

        # Calculate the tail period
        tail_start_time: datetime | None = None
        tail_end_time: datetime | None = None
        if end_time is None:
            tail_start_time = _last_statistic(session, Statistics, metadata_id)
            if tail_start_time:
                tail_start_time += Statistics.duration
            else:
                tail_start_time = now.replace(minute=0, second=0, microsecond=0)
        elif tail_only:
            tail_start_time = start_time
            tail_end_time = end_time
        elif end_time.minute:
            tail_start_time = end_time.replace(minute=0, second=0, microsecond=0)
            tail_end_time = end_time

        # Calculate the main period
        main_start_time: datetime | None = None
        main_end_time: datetime | None = None
        if not tail_only:
            main_start_time = start_time if head_end_time is None else head_end_time
            main_end_time = end_time if tail_start_time is None else tail_start_time

        if not types.isdisjoint({"max", "mean", "min"}):
            result = _get_max_mean_min_statistic(
                session,
                head_start_time,
                head_end_time,
                main_start_time,
                main_end_time,
                tail_start_time,
                tail_end_time,
                tail_only,
                metadata,
                types,
            )

        if "change" in types:
            oldest_sum: float | None
            if start_time is None:
                oldest_sum = 0.0
            else:
                oldest_sum = _get_oldest_sum_statistic(
                    session,
                    head_start_time,
                    main_start_time,
                    tail_start_time,
                    oldest_stat,
                    oldest_5_min_stat,
                    tail_only,
                    metadata_id,
                )
            newest_sum = _get_newest_sum_statistic(
                session,
                head_start_time,
                head_end_time,
                main_start_time,
                main_end_time,
                tail_start_time,
                tail_end_time,
                tail_only,
                metadata_id,
            )
            # Calculate the difference between the oldest and newest sum
            if oldest_sum is not None and newest_sum is not None:
                result["change"] = newest_sum - oldest_sum
            else:
                result["change"] = None

    unit_class = metadata[1]["unit_class"]
    state_unit = unit = metadata[1]["unit_of_measurement"]
    if state := hass.states.get(statistic_id):
        state_unit = state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
    convert = _get_statistic_to_display_unit_converter(
        unit_class, unit, state_unit, units
    )

    if not convert:
        return result
    return {key: convert(value) for key, value in result.items()}