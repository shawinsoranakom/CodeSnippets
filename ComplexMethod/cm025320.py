async def ws_stream(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Handle history stream websocket command."""
    start_time_str = msg["start_time"]
    msg_id: int = msg["id"]
    utc_now = dt_util.utcnow()

    if start_time := dt_util.parse_datetime(start_time_str):
        start_time = dt_util.as_utc(start_time)

    if not start_time or start_time > utc_now:
        connection.send_error(msg_id, "invalid_start_time", "Invalid start_time")
        return

    end_time_str = msg.get("end_time")
    end_time: dt | None = None
    if end_time_str:
        if not (end_time := dt_util.parse_datetime(end_time_str)):
            connection.send_error(msg_id, "invalid_end_time", "Invalid end_time")
            return
        end_time = dt_util.as_utc(end_time)
        if end_time < start_time:
            connection.send_error(msg_id, "invalid_end_time", "Invalid end_time")
            return

    entity_ids: list[str] = msg["entity_ids"]
    for entity_id in entity_ids:
        if not hass.states.get(entity_id) and not valid_entity_id(entity_id):
            connection.send_error(msg["id"], "invalid_entity_ids", "Invalid entity_ids")
            return

    include_start_time_state = msg["include_start_time_state"]
    significant_changes_only = msg["significant_changes_only"]
    no_attributes = msg["no_attributes"]
    minimal_response = msg["minimal_response"]

    if end_time and end_time <= utc_now:
        if (
            not include_start_time_state
            and entity_ids
            and not entities_may_have_state_changes_after(
                hass, entity_ids, start_time, no_attributes
            )
        ):
            _async_send_empty_response(connection, msg_id, start_time, end_time)
            return

        connection.subscriptions[msg_id] = callback(lambda: None)
        connection.send_result(msg_id)
        await _async_send_historical_states(
            hass,
            connection,
            msg_id,
            start_time,
            end_time,
            entity_ids,
            include_start_time_state,
            significant_changes_only,
            minimal_response,
            no_attributes,
            True,
        )
        return

    subscriptions: list[CALLBACK_TYPE] = []
    stream_queue: asyncio.Queue[Event] = asyncio.Queue(MAX_PENDING_HISTORY_STATES)
    live_stream = HistoryLiveStream(
        subscriptions=subscriptions, stream_queue=stream_queue
    )

    @callback
    def _unsub(*_utc_time: Any) -> None:
        """Unsubscribe from all events."""
        for subscription in subscriptions:
            subscription()
        subscriptions.clear()
        if live_stream.task:
            live_stream.task.cancel()
        if live_stream.wait_sync_future:
            live_stream.wait_sync_future.cancel()
        if live_stream.end_time_unsub:
            live_stream.end_time_unsub()
            live_stream.end_time_unsub = None

    if end_time:
        live_stream.end_time_unsub = async_track_point_in_utc_time(
            hass, _unsub, end_time
        )

    @callback
    def _queue_or_cancel(event: Event) -> None:
        """Queue an event to be processed or cancel."""
        try:
            stream_queue.put_nowait(event)
        except asyncio.QueueFull:
            _LOGGER.debug(
                "Client exceeded max pending messages of %s",
                MAX_PENDING_HISTORY_STATES,
            )
            _unsub()

    _async_subscribe_events(
        hass,
        subscriptions,
        _queue_or_cancel,
        entity_ids,
        significant_changes_only=significant_changes_only,
        minimal_response=minimal_response,
    )
    subscriptions_setup_complete_time = dt_util.utcnow()
    connection.subscriptions[msg_id] = _unsub
    connection.send_result(msg_id)
    # Fetch everything from history
    last_event_time = await _async_send_historical_states(
        hass,
        connection,
        msg_id,
        start_time,
        subscriptions_setup_complete_time,
        entity_ids,
        include_start_time_state,
        significant_changes_only,
        minimal_response,
        no_attributes,
        True,
    )

    if msg_id not in connection.subscriptions:
        # Unsubscribe happened while sending historical states
        return

    live_stream.task = create_eager_task(
        _async_events_consumer(
            subscriptions_setup_complete_time,
            connection,
            msg_id,
            stream_queue,
            no_attributes,
        )
    )

    if sync_future := get_instance(hass).async_get_commit_future():
        # Set the future so we can cancel it if the client
        # unsubscribes before the commit is done so we don't
        # query the database needlessly
        live_stream.wait_sync_future = sync_future
        await live_stream.wait_sync_future

    #
    # Fetch any states from the database that have
    # not been committed since the original fetch
    # so we can switch over to using the subscriptions
    #
    # We only want states that happened after the last state
    # we had from the last database query
    #
    await _async_send_historical_states(
        hass,
        connection,
        msg_id,
        # Add one microsecond so we are outside the window of
        # the last event we got from the database since otherwise
        # we could fetch the same event twice
        (last_event_time or start_time) + timedelta(microseconds=1),
        subscriptions_setup_complete_time,
        entity_ids,
        False,  # We don't want the start time state again
        significant_changes_only,
        minimal_response,
        no_attributes,
        send_empty=not last_event_time,
    )