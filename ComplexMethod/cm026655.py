async def _async_send_historical_events(
    hass: HomeAssistant,
    connection: ActiveConnection,
    msg_id: int,
    start_time: dt,
    end_time: dt,
    event_processor: EventProcessor,
    partial: bool,
    force_send: bool = False,
) -> dt | None:
    """Select historical data from the database and deliver it to the websocket.

    If the query is considered a big query we will split the request into
    two chunks so that they get the recent events first and the select
    that is expected to take a long time comes in after to ensure
    they are not stuck at a loading screen and can start looking at
    the data right away.

    This function returns the time of the most recent event we sent to the
    websocket.
    """
    is_big_query = (
        not event_processor.entity_ids
        and not event_processor.device_ids
        and ((end_time - start_time) > timedelta(hours=BIG_QUERY_HOURS))
    )

    if not is_big_query:
        message, last_event_time = await _async_get_ws_stream_events(
            hass,
            msg_id,
            start_time,
            end_time,
            event_processor,
            partial,
        )
        # If there is no last_event_time, there are no historical
        # results, but we still send an empty message
        # if its the last one (not partial) so
        # consumers of the api know their request was
        # answered but there were no results
        if last_event_time or not partial or force_send:
            connection.send_message(message)
        return last_event_time

    # This is a big query so we deliver
    # the first three hours and then
    # we fetch the old data
    recent_query_start = end_time - timedelta(hours=BIG_QUERY_RECENT_HOURS)
    recent_message, recent_query_last_event_time = await _async_get_ws_stream_events(
        hass,
        msg_id,
        recent_query_start,
        end_time,
        event_processor,
        partial=True,
    )
    if recent_query_last_event_time:
        connection.send_message(recent_message)

    older_message, older_query_last_event_time = await _async_get_ws_stream_events(
        hass,
        msg_id,
        start_time,
        recent_query_start,
        event_processor,
        partial,
    )
    # If there is no last_event_time, there are no historical
    # results, but we still send an empty message
    # if its the last one (not partial) so
    # consumers of the api know their request was
    # answered but there were no results
    if older_query_last_event_time or not partial or force_send:
        connection.send_message(older_message)

    # Returns the time of the newest event
    return recent_query_last_event_time or older_query_last_event_time