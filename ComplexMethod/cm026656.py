async def ws_event_stream(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Handle logbook stream events websocket command."""
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

    device_ids = msg.get("device_ids")
    entity_ids = msg.get("entity_ids")
    if entity_ids:
        entity_ids = async_filter_entities(hass, entity_ids)
        if not entity_ids and not device_ids:
            _async_send_empty_response(connection, msg_id, start_time, end_time)
            return

    event_types = async_determine_event_types(hass, entity_ids, device_ids)
    # A past end_time makes this a one-shot fetch that never goes live.
    will_go_live = not (end_time and end_time <= utc_now)
    event_processor = EventProcessor(
        hass,
        event_types,
        entity_ids,
        device_ids,
        None,
        timestamp=True,
        include_entity_name=False,
        for_live_stream=will_go_live,
    )

    if end_time and end_time <= utc_now:
        # Not live stream but we it might be a big query
        connection.subscriptions[msg_id] = callback(lambda: None)
        connection.send_result(msg_id)
        # Fetch everything from history
        await _async_send_historical_events(
            hass,
            connection,
            msg_id,
            start_time,
            end_time,
            event_processor,
            partial=False,
        )
        return

    subscriptions: list[CALLBACK_TYPE] = []
    stream_queue: asyncio.Queue[Event] = asyncio.Queue(MAX_PENDING_LOGBOOK_EVENTS)
    live_stream = LogbookLiveStream(
        subscriptions=subscriptions, stream_queue=stream_queue
    )

    @callback
    def _unsub(*time: Any) -> None:
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
                MAX_PENDING_LOGBOOK_EVENTS,
            )
            _unsub()

    entities_filter: Callable[[str], bool] | None = None
    if not event_processor.limited_select:
        logbook_config: LogbookConfig = hass.data[DOMAIN]
        entities_filter = logbook_config.entity_filter

    # Live subscription needs call_service events so the live consumer can
    # cache parent user_ids as they fire. Historical queries don't — the
    # context_only join fetches them by context_id regardless of type.
    # Unfiltered streams already include it via BUILT_IN_EVENTS.
    async_subscribe_events(
        hass,
        subscriptions,
        _queue_or_cancel,
        {*event_types, EVENT_CALL_SERVICE},
        entities_filter,
        entity_ids,
        device_ids,
    )
    subscriptions_setup_complete_time = dt_util.utcnow()
    connection.subscriptions[msg_id] = _unsub
    connection.send_result(msg_id)
    # Fetch everything from history
    last_event_time = await _async_send_historical_events(
        hass,
        connection,
        msg_id,
        start_time,
        subscriptions_setup_complete_time,
        event_processor,
        partial=True,
        # Force a send since the wait for the sync task
        # can take a a while if the recorder is busy and
        # we want to make sure the client is not still spinning
        # because it is waiting for the first message
        force_send=True,
    )

    if msg_id not in connection.subscriptions:
        # Unsubscribe happened while sending historical events
        return

    live_stream.task = create_eager_task(
        _async_events_consumer(
            subscriptions_setup_complete_time,
            connection,
            msg_id,
            stream_queue,
            event_processor,
        )
    )

    if sync_future := get_instance(hass).async_get_commit_future():
        # Set the future so we can cancel it if the client
        # unsubscribes before the commit is done so we don't
        # query the database needlessly
        live_stream.wait_sync_future = sync_future
        await live_stream.wait_sync_future

    #
    # Fetch any events from the database that have
    # not been committed since the original fetch
    # so we can switch over to using the subscriptions
    #
    # We only want events that happened after the last event
    # we had from the last database query
    #
    await _async_send_historical_events(
        hass,
        connection,
        msg_id,
        # Add one microsecond so we are outside the window of
        # the last event we got from the database since otherwise
        # we could fetch the same event twice
        (last_event_time or start_time) + timedelta(microseconds=1),
        subscriptions_setup_complete_time,
        event_processor,
        partial=False,
    )
    event_processor.switch_to_live()