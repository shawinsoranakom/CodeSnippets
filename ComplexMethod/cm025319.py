async def ws_get_history_during_period(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Handle history during period websocket command."""
    start_time_str = msg["start_time"]
    end_time_str = msg.get("end_time")

    if start_time := dt_util.parse_datetime(start_time_str):
        start_time = dt_util.as_utc(start_time)
    else:
        connection.send_error(msg["id"], "invalid_start_time", "Invalid start_time")
        return

    if end_time_str:
        if end_time := dt_util.parse_datetime(end_time_str):
            end_time = dt_util.as_utc(end_time)
        else:
            connection.send_error(msg["id"], "invalid_end_time", "Invalid end_time")
            return
    else:
        end_time = None

    if start_time > dt_util.utcnow():
        connection.send_result(msg["id"], {})
        return

    entity_ids: list[str] = msg["entity_ids"]
    for entity_id in entity_ids:
        if not hass.states.get(entity_id) and not valid_entity_id(entity_id):
            connection.send_error(msg["id"], "invalid_entity_ids", "Invalid entity_ids")
            return

    include_start_time_state = msg["include_start_time_state"]
    no_attributes = msg["no_attributes"]

    if (
        # has_states_before will return True if there are states older than
        # end_time. If it's false, we know there are no states in the
        # database up until end_time.
        (end_time and not has_states_before(hass, end_time))
        or (
            not include_start_time_state
            and entity_ids
            and not entities_may_have_state_changes_after(
                hass, entity_ids, start_time, no_attributes
            )
        )
    ):
        connection.send_result(msg["id"], {})
        return

    significant_changes_only = msg["significant_changes_only"]
    minimal_response = msg["minimal_response"]

    connection.send_message(
        await get_instance(hass).async_add_executor_job(
            _ws_get_significant_states,
            hass,
            msg["id"],
            start_time,
            end_time,
            entity_ids,
            include_start_time_state,
            significant_changes_only,
            minimal_response,
            no_attributes,
        )
    )