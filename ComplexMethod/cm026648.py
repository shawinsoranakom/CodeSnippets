def _humanify(
    hass: HomeAssistant,
    rows: Generator[EventAsRow] | Sequence[Row] | Result,
    ent_reg: er.EntityRegistry,
    logbook_run: LogbookRun,
    context_augmenter: ContextAugmenter,
    query_parent_user_ids: dict[bytes, bytes] | None,
) -> Generator[dict[str, Any]]:
    """Generate a converted list of events into entries."""
    # Continuous sensors, will be excluded from the logbook
    continuous_sensors: dict[str, bool] = {}
    context_lookup = logbook_run.context_lookup
    external_events = logbook_run.external_events
    event_cache_get = logbook_run.event_cache.get
    entity_name_cache_get = logbook_run.entity_name_cache.get
    include_entity_name = logbook_run.include_entity_name
    timestamp = logbook_run.timestamp
    memoize_new_contexts = logbook_run.memoize_new_contexts
    get_context = context_augmenter.get_context
    context_id_bin: bytes
    data: dict[str, Any]

    context_user_ids = logbook_run.context_user_ids
    # Skip the LRU write on one-shot runs — the LogbookRun is discarded.
    populate_context_user_ids = logbook_run.for_live_stream

    # Process rows
    for row in rows:
        context_id_bin = row[CONTEXT_ID_BIN_POS]
        if memoize_new_contexts and context_id_bin not in context_lookup:
            context_lookup[context_id_bin] = row
        if (
            populate_context_user_ids
            and (context_user_id_bin := row[CONTEXT_USER_ID_BIN_POS])
            and context_id_bin not in context_user_ids
        ):
            context_user_ids[context_id_bin] = context_user_id_bin
        if row[CONTEXT_ONLY_POS]:
            continue
        event_type = row[EVENT_TYPE_POS]
        if event_type == EVENT_CALL_SERVICE:
            continue

        if event_type is PSEUDO_EVENT_STATE_CHANGED:
            entity_id = row[ENTITY_ID_POS]
            if TYPE_CHECKING:
                assert entity_id is not None
            # Skip continuous sensors
            if (
                is_continuous := continuous_sensors.get(entity_id)
            ) is None and split_entity_id(entity_id)[0] == SENSOR_DOMAIN:
                is_continuous = is_sensor_continuous(hass, ent_reg, entity_id)
                continuous_sensors[entity_id] = is_continuous
            if is_continuous:
                continue

            data = {
                LOGBOOK_ENTRY_STATE: row[STATE_POS],
                LOGBOOK_ENTRY_ENTITY_ID: entity_id,
            }
            if include_entity_name:
                data[LOGBOOK_ENTRY_NAME] = entity_name_cache_get(entity_id)
            if icon := row[ICON_POS]:
                data[LOGBOOK_ENTRY_ICON] = icon

        elif event_type in external_events:
            domain, describe_event = external_events[event_type]
            try:
                data = describe_event(event_cache_get(row))
            except Exception:
                _LOGGER.exception(
                    "Error with %s describe event for %s", domain, event_type
                )
                continue
            data[LOGBOOK_ENTRY_DOMAIN] = domain

        elif event_type == EVENT_LOGBOOK_ENTRY:
            event = event_cache_get(row)
            if not (event_data := event.data):
                continue
            entry_domain = event_data.get(ATTR_DOMAIN)
            entry_entity_id = event_data.get(ATTR_ENTITY_ID)
            if entry_domain is None and entry_entity_id is not None:
                entry_domain = split_entity_id(str(entry_entity_id))[0]
            data = {
                LOGBOOK_ENTRY_NAME: event_data.get(ATTR_NAME),
                LOGBOOK_ENTRY_MESSAGE: event_data.get(ATTR_MESSAGE),
                LOGBOOK_ENTRY_DOMAIN: entry_domain,
                LOGBOOK_ENTRY_ENTITY_ID: entry_entity_id,
            }

        else:
            continue

        row_time_fired_ts = row[TIME_FIRED_TS_POS]
        # Explicit None check: 0.0 is a valid epoch.
        time_fired_ts: float = (
            row_time_fired_ts if row_time_fired_ts is not None else time.time()
        )
        if timestamp:
            when: str | float = time_fired_ts
        else:
            when = process_timestamp_to_utc_isoformat(
                dt_util.utc_from_timestamp(time_fired_ts)
            )
        data[LOGBOOK_ENTRY_WHEN] = when

        if context_user_id_bin := row[CONTEXT_USER_ID_BIN_POS]:
            data[CONTEXT_USER_ID] = bytes_to_uuid_hex_or_none(context_user_id_bin)

        # Augment context if its available but not if the context is the same as the row
        # or if the context is the parent of the row
        if (context_row := get_context(context_id_bin, row)) and not (
            (row is context_row or _rows_ids_match(row, context_row))
            and (
                not (context_parent := row[CONTEXT_PARENT_ID_BIN_POS])
                or not (context_row := get_context(context_parent, context_row))
                or row is context_row
                or _rows_ids_match(row, context_row)
            )
        ):
            context_augmenter.augment(data, context_row)

        # Fall back to the parent context for child contexts that inherit
        # user attribution (e.g., generic_thermostat -> switch turn_on).
        # Read from context_lookup directly instead of get_context() to
        # avoid the origin_event fallback which would return the *child*
        # row's origin event, not the parent's.
        if CONTEXT_USER_ID not in data and (
            context_parent_id_bin := row[CONTEXT_PARENT_ID_BIN_POS]
        ):
            parent_user_id_bin: bytes | None = context_user_ids.get(
                context_parent_id_bin
            )
            if parent_user_id_bin is None and query_parent_user_ids is not None:
                parent_user_id_bin = query_parent_user_ids.get(context_parent_id_bin)
            if (
                parent_user_id_bin is None
                and (parent_row := context_lookup.get(context_parent_id_bin))
                is not None
            ):
                parent_user_id_bin = parent_row[CONTEXT_USER_ID_BIN_POS]
            if parent_user_id_bin:
                data[CONTEXT_USER_ID] = bytes_to_uuid_hex_or_none(parent_user_id_bin)

        yield data