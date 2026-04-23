async def async_predict_common_control(
    hass: HomeAssistant, user_id: str
) -> EntityUsagePredictions:
    """Generate a list of commonly used entities for a user.

    Args:
        hass: Home Assistant instance
        user_id: User ID to filter events by.
    """
    # Get the recorder instance to ensure it's ready
    recorder = get_instance(hass)
    ent_reg = er.async_get(hass)

    # Execute the database operation in the recorder's executor
    data = await recorder.async_add_executor_job(
        _fetch_with_session, hass, _fetch_and_process_data, ent_reg, user_id
    )
    # Prepare a dictionary to track results
    results: dict[str, Counter[str]] = {
        time_cat: Counter() for time_cat in TIME_CATEGORIES
    }

    allowed_entities = set(hass.states.async_entity_ids(ALLOWED_DOMAINS))
    hidden_entities: set[str] = set()

    # Keep track of contexts that we processed so that we will only process
    # the first service call in a context, and not subsequent calls.
    context_processed: set[bytes] = set()
    # Execute the query
    context_id: bytes
    time_fired_ts: float
    shared_data: str | None
    local_time_zone = dt_util.get_default_time_zone()
    for context_id, time_fired_ts, shared_data in data:
        # Skip if we have already processed an event that was part of this context
        if context_id in context_processed:
            continue

        # Mark this context as processed
        context_processed.add(context_id)

        # Parse the event data
        if not time_fired_ts or not shared_data:
            continue

        try:
            event_data = json_loads_object(shared_data)
        except (ValueError, TypeError) as err:
            _LOGGER.debug("Failed to parse event data: %s", err)
            continue

        # Empty event data, skipping
        if not event_data:
            continue

        service_data = cast(dict[str, Any] | None, event_data.get("service_data"))

        # No service data found, skipping
        if not service_data:
            continue

        entity_ids: str | list[str] | None = service_data.get("entity_id")

        # No entity IDs found, skip this event
        if entity_ids is None:
            continue

        if not isinstance(entity_ids, list):
            entity_ids = [entity_ids]

        # Convert to local time for time category determination
        period = time_category(
            datetime.fromtimestamp(time_fired_ts, local_time_zone).hour
        )
        period_results = results[period]

        # Count entity usage
        for entity_id in entity_ids:
            if entity_id not in allowed_entities or entity_id in hidden_entities:
                continue

            if (
                entity_id not in period_results
                and (entry := ent_reg.async_get(entity_id))
                and entry.hidden
            ):
                hidden_entities.add(entity_id)
                continue

            period_results[entity_id] += 1

    return EntityUsagePredictions(
        morning=[
            ent_id for (ent_id, _) in results["morning"].most_common(RESULTS_TO_INCLUDE)
        ],
        afternoon=[
            ent_id
            for (ent_id, _) in results["afternoon"].most_common(RESULTS_TO_INCLUDE)
        ],
        evening=[
            ent_id for (ent_id, _) in results["evening"].most_common(RESULTS_TO_INCLUDE)
        ],
        night=[
            ent_id for (ent_id, _) in results["night"].most_common(RESULTS_TO_INCLUDE)
        ],
    )