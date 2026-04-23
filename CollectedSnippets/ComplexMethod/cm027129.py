def _augment_result_with_change(
    hass: HomeAssistant,
    session: Session,
    start_time: datetime,
    units: dict[str, str] | None,
    _types: set[Literal["change", "last_reset", "max", "mean", "min", "state", "sum"]],
    table: type[Statistics | StatisticsShortTerm],
    metadata: dict[str, tuple[int, StatisticMetaData]],
    result: dict[str, list[StatisticsRow]],
) -> None:
    """Add change to the result."""
    drop_sum = "sum" not in _types
    prev_sums = {}
    if tmp := _statistics_at_time(
        get_instance(hass),
        session,
        {metadata[statistic_id][0] for statistic_id in result},
        table,
        start_time,
        {"sum"},
    ):
        _metadata = dict(metadata.values())
        for row in tmp:
            metadata_by_id = _metadata[row.metadata_id]
            statistic_id = metadata_by_id["statistic_id"]

            unit_class = metadata_by_id["unit_class"]
            state_unit = unit = metadata_by_id["unit_of_measurement"]
            if state := hass.states.get(statistic_id):
                state_unit = state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
            convert = _get_statistic_to_display_unit_converter(
                unit_class, unit, state_unit, units
            )

            if convert is not None:
                prev_sums[statistic_id] = convert(row.sum)
            else:
                prev_sums[statistic_id] = row.sum

    for statistic_id, rows in result.items():
        prev_sum = prev_sums.get(statistic_id) or 0
        for statistics_row in rows:
            if "sum" not in statistics_row:
                continue
            if drop_sum:
                _sum = statistics_row.pop("sum")
            else:
                _sum = statistics_row["sum"]
            if _sum is None:
                statistics_row["change"] = None
                continue
            statistics_row["change"] = _sum - prev_sum
            prev_sum = _sum