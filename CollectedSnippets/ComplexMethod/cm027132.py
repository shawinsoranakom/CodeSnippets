def _sorted_statistics_to_dict(
    hass: HomeAssistant,
    stats: Sequence[Row[Any]],
    statistic_ids: set[str] | None,
    _metadata: dict[str, tuple[int, StatisticMetaData]],
    convert_units: bool,
    table: type[StatisticsBase],
    units: dict[str, str] | None,
    types: set[Literal["last_reset", "max", "mean", "min", "state", "sum"]],
) -> dict[str, list[StatisticsRow]]:
    """Convert SQL results into JSON friendly data structure."""
    assert stats, "stats must not be empty"  # Guard against implementation error
    result: dict[str, list[StatisticsRow]] = defaultdict(list)
    metadata = dict(_metadata.values())
    # Identify metadata IDs for which no data was available at the requested start time
    field_map: dict[str, int] = {key: idx for idx, key in enumerate(stats[0]._fields)}
    metadata_id_idx = field_map["metadata_id"]
    start_ts_idx = field_map["start_ts"]
    stats_by_meta_id: dict[int, list[Row]] = {}
    seen_statistic_ids: set[str] = set()
    key_func = itemgetter(metadata_id_idx)
    for meta_id, group in groupby(stats, key_func):
        stats_by_meta_id[meta_id] = list(group)
        seen_statistic_ids.add(metadata[meta_id]["statistic_id"])

    # Set all statistic IDs to empty lists in result set to maintain the order
    if statistic_ids is not None:
        for stat_id in statistic_ids:
            # Only set the statistic ID if it is in the data to
            # avoid having to do a second loop to remove the
            # statistic IDs that are not in the data at the end
            if stat_id in seen_statistic_ids:
                result[stat_id] = []

    # Figure out which fields we need to extract from the SQL result
    # and which indices they have in the result so we can avoid the overhead
    # of doing a dict lookup for each row
    if "last_reset_ts" in field_map:
        field_map["last_reset"] = field_map.pop("last_reset_ts")
    sum_idx = field_map["sum"] if "sum" in types else None
    sum_only = len(types) == 1 and sum_idx is not None
    row_mapping = tuple(
        (column, field_map[column])
        for key in types
        for column in ({key, *_type_column_mapping.get(key, ())})
        if column in field_map
    )
    # Append all statistic entries, and optionally do unit conversion
    table_duration_seconds = table.duration.total_seconds()
    for meta_id, db_rows in stats_by_meta_id.items():
        metadata_by_id = metadata[meta_id]
        statistic_id = metadata_by_id["statistic_id"]
        if convert_units:
            unit_class = metadata_by_id["unit_class"]
            state_unit = unit = metadata_by_id["unit_of_measurement"]
            if state := hass.states.get(statistic_id):
                state_unit = state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
            convert = _get_statistic_to_display_unit_converter(
                unit_class, unit, state_unit, units, allow_none=False
            )
        else:
            convert = None

        build_args = (db_rows, table_duration_seconds, start_ts_idx)
        if sum_only:
            # This function is extremely flexible and can handle all types of
            # statistics, but in practice we only ever use a few combinations.
            #
            # For energy, we only need sum statistics, so we can optimize
            # this path to avoid the overhead of the more generic function.
            assert sum_idx is not None
            if convert:
                _stats = _build_sum_converted_stats(*build_args, sum_idx, convert)
            else:
                _stats = _build_sum_stats(*build_args, sum_idx)
        elif convert:
            _stats = _build_converted_stats(*build_args, row_mapping, convert)
        else:
            _stats = _build_stats(*build_args, row_mapping)

        result[statistic_id] = _stats

    return result