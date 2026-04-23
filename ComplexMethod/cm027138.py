def _sorted_states_to_dict(
    states: Iterable[Row],
    start_time_ts: float | None,
    entity_ids: list[str],
    entity_id_to_metadata_id: dict[str, int | None],
    minimal_response: bool = False,
    compressed_state_format: bool = False,
    descending: bool = False,
    no_attributes: bool = False,
) -> dict[str, list[State | dict[str, Any]]]:
    """Convert SQL results into JSON friendly data structure.

    This takes our state list and turns it into a JSON friendly data
    structure {'entity_id': [list of states], 'entity_id2': [list of states]}

    States must be sorted by entity_id and last_updated

    We also need to go back and create a synthetic zero data point for
    each list of states, otherwise our graphs won't start on the Y
    axis correctly.
    """
    field_map = _FIELD_MAP
    state_class: Callable[
        [Row, dict[str, dict[str, Any]], float | None, str, str, float | None, bool],
        State | dict[str, Any],
    ]
    if compressed_state_format:
        state_class = row_to_compressed_state
        attr_time = COMPRESSED_STATE_LAST_UPDATED
        attr_state = COMPRESSED_STATE_STATE
    else:
        state_class = LazyState
        attr_time = LAST_CHANGED_KEY
        attr_state = STATE_KEY

    # Set all entity IDs to empty lists in result set to maintain the order
    result: dict[str, list[State | dict[str, Any]]] = {
        entity_id: [] for entity_id in entity_ids
    }
    metadata_id_to_entity_id: dict[int, str] = {}
    metadata_id_to_entity_id = {
        v: k for k, v in entity_id_to_metadata_id.items() if v is not None
    }
    # Get the states at the start time
    if len(entity_ids) == 1:
        metadata_id = entity_id_to_metadata_id[entity_ids[0]]
        assert metadata_id is not None  # should not be possible if we got here
        states_iter: Iterable[tuple[int, Iterator[Row]]] = (
            (metadata_id, iter(states)),
        )
    else:
        key_func = itemgetter(field_map["metadata_id"])
        states_iter = groupby(states, key_func)

    state_idx = field_map["state"]
    last_updated_ts_idx = field_map["last_updated_ts"]

    # Append all changes to it
    for metadata_id, group in states_iter:
        entity_id = metadata_id_to_entity_id[metadata_id]
        attr_cache: dict[str, dict[str, Any]] = {}
        ent_results = result[entity_id]
        if (
            not minimal_response
            or split_entity_id(entity_id)[0] in NEED_ATTRIBUTE_DOMAINS
        ):
            ent_results.extend(
                [
                    state_class(
                        db_state,
                        attr_cache,
                        start_time_ts,
                        entity_id,
                        db_state[state_idx],
                        db_state[last_updated_ts_idx],
                        False,
                    )
                    for db_state in group
                ]
            )
            continue

        prev_state: str | None = None
        # With minimal response we only provide a native
        # State for the first and last response. All the states
        # in-between only provide the "state" and the
        # "last_changed".
        if not ent_results:
            if (first_state := next(group, None)) is None:
                continue
            prev_state = first_state[state_idx]
            ent_results.append(
                state_class(
                    first_state,
                    attr_cache,
                    start_time_ts,
                    entity_id,
                    prev_state,
                    first_state[last_updated_ts_idx],
                    no_attributes,
                )
            )

        #
        # minimal_response only makes sense with last_updated == last_updated
        #
        # We use last_updated for for last_changed since its the same
        #
        # With minimal response we do not care about attribute
        # changes so we can filter out duplicate states
        if compressed_state_format:
            # Compressed state format uses the timestamp directly
            ent_results.extend(
                [
                    {
                        attr_state: (prev_state := state),
                        attr_time: row[last_updated_ts_idx],
                    }
                    for row in group
                    if (state := row[state_idx]) != prev_state
                ]
            )
            continue

        # Non-compressed state format returns an ISO formatted string
        _utc_from_timestamp = dt_util.utc_from_timestamp
        ent_results.extend(
            [
                {
                    attr_state: (prev_state := state),
                    attr_time: _utc_from_timestamp(
                        row[last_updated_ts_idx]
                    ).isoformat(),
                }
                for row in group
                if (state := row[state_idx]) != prev_state
            ]
        )

    if descending:
        for ent_results in result.values():
            ent_results.reverse()

    # Filter out the empty lists if some states had 0 results.
    return {key: val for key, val in result.items() if val}