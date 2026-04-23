def get_significant_states_with_session(
    hass: HomeAssistant,
    session: Session,
    start_time: datetime,
    end_time: datetime | None = None,
    entity_ids: list[str] | None = None,
    filters: Filters | None = None,
    include_start_time_state: bool = True,
    significant_changes_only: bool = True,
    minimal_response: bool = False,
    no_attributes: bool = False,
    compressed_state_format: bool = False,
) -> dict[str, list[State | dict[str, Any]]]:
    """Return states changes during UTC period start_time - end_time.

    entity_ids is an optional iterable of entities to include in the results.

    filters is an optional SQLAlchemy filter which will be applied to the database
    queries unless entity_ids is given, in which case its ignored.

    Significant states are all states where there is a state change,
    as well as all states from certain domains (for instance
    thermostat so that we get current temperature in our graphs).
    """
    if filters is not None:
        raise NotImplementedError("Filters are no longer supported")
    if not entity_ids:
        raise ValueError("entity_ids must be provided")
    entity_id_to_metadata_id: dict[str, int | None] | None = None
    metadata_ids_in_significant_domains: list[int] = []
    instance = get_instance(hass)
    if not (
        entity_id_to_metadata_id := instance.states_meta_manager.get_many(
            entity_ids, session, False
        )
    ) or not (possible_metadata_ids := extract_metadata_ids(entity_id_to_metadata_id)):
        return {}
    metadata_ids = possible_metadata_ids
    if significant_changes_only:
        metadata_ids_in_significant_domains = [
            metadata_id
            for entity_id, metadata_id in entity_id_to_metadata_id.items()
            if metadata_id is not None
            and split_entity_id(entity_id)[0] in SIGNIFICANT_DOMAINS
        ]
    oldest_ts: float | None = None
    if include_start_time_state and not (
        oldest_ts := _get_oldest_possible_ts(hass, start_time)
    ):
        include_start_time_state = False
    start_time_ts = start_time.timestamp()
    end_time_ts = datetime_to_timestamp_or_none(end_time)
    single_metadata_id = metadata_ids[0] if len(metadata_ids) == 1 else None
    rows: list[Row] = []
    if TYPE_CHECKING:
        assert instance.database_engine is not None
    slow_dependent_subquery = instance.database_engine.optimizer.slow_dependent_subquery
    if include_start_time_state and slow_dependent_subquery:
        # https://github.com/home-assistant/core/issues/137178
        # If we include the start time state we need to limit the
        # number of metadata_ids we query for at a time to avoid
        # hitting limits in the MySQL optimizer that prevent
        # the start time state query from using an index-only optimization
        # to find the start time state.
        iter_metadata_ids = chunked_or_all(metadata_ids, MAX_IDS_FOR_INDEXED_GROUP_BY)
    else:
        iter_metadata_ids = (metadata_ids,)
    for metadata_ids_chunk in iter_metadata_ids:
        stmt = _generate_significant_states_with_session_stmt(
            start_time_ts,
            end_time_ts,
            single_metadata_id,
            metadata_ids_chunk,
            metadata_ids_in_significant_domains,
            significant_changes_only,
            no_attributes,
            include_start_time_state,
            oldest_ts,
            slow_dependent_subquery,
        )
        row_chunk = cast(
            list[Row],
            execute_stmt_lambda_element(session, stmt, None, end_time, orm_rows=False),
        )
        if rows:
            rows += row_chunk
        else:
            # If we have no rows yet, we can just assign the chunk
            # as this is the common case since its rare that
            # we exceed the MAX_IDS_FOR_INDEXED_GROUP_BY limit
            rows = row_chunk
    return _sorted_states_to_dict(
        rows,
        start_time_ts if include_start_time_state else None,
        entity_ids,
        entity_id_to_metadata_id,
        minimal_response,
        compressed_state_format,
        no_attributes=no_attributes,
    )