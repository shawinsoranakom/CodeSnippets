async def ws_start_preview(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Generate a preview."""
    if msg["flow_type"] == "config_flow":
        flow_status = hass.config_entries.flow.async_get(msg["flow_id"])
        flow_sets = hass.config_entries.flow._handler_progress_index.get(  # noqa: SLF001
            flow_status["handler"]
        )
        options = {}
        assert flow_sets
        for active_flow in flow_sets:
            options = active_flow._common_handler.options  # type: ignore [attr-defined] # noqa: SLF001
        config_entry = hass.config_entries.async_get_entry(flow_status["handler"])
        entity_id = options[CONF_ENTITY_ID]
        name = options[CONF_NAME]
        conf_type = options[CONF_TYPE]
    else:
        flow_status = hass.config_entries.options.async_get(msg["flow_id"])
        config_entry = hass.config_entries.async_get_entry(flow_status["handler"])
        if not config_entry:
            raise HomeAssistantError("Config entry not found")
        entity_id = config_entry.options[CONF_ENTITY_ID]
        name = config_entry.options[CONF_NAME]
        conf_type = config_entry.options[CONF_TYPE]

    @callback
    def async_preview_updated(
        last_exception: BaseException | None, state: str, attributes: Mapping[str, Any]
    ) -> None:
        """Forward config entry state events to websocket."""
        if last_exception:
            connection.send_message(
                websocket_api.event_message(
                    msg["id"], {"error": str(last_exception) or "Unknown error"}
                )
            )
        else:
            connection.send_message(
                websocket_api.event_message(
                    msg["id"], {"attributes": attributes, "state": state}
                )
            )

    for param in CONF_PERIOD_KEYS:
        if param in msg["user_input"] and not bool(msg["user_input"][param]):
            del msg["user_input"][param]  # Remove falsy values before counting keys

    validated_data: Any = None
    try:
        validated_data = (_get_options_schema_with_entity_id(entity_id, conf_type))(
            msg["user_input"]
        )
    except vol.Invalid as ex:
        connection.send_error(msg["id"], "invalid_schema", str(ex))
        return

    try:
        _validate_two_period_keys(validated_data)
    except SchemaFlowError:
        connection.send_error(
            msg["id"],
            "invalid_schema",
            f"Exactly two of {', '.join(CONF_PERIOD_KEYS)} required",
        )
        return

    sensor_type = validated_data.get(CONF_TYPE)
    entity_states = validated_data.get(CONF_STATE)
    start = validated_data.get(CONF_START)
    end = validated_data.get(CONF_END)
    duration = validated_data.get(CONF_DURATION)
    advanced_settings = validated_data.get(SECTION_ADVANCED_SETTINGS, {})
    min_state_duration = advanced_settings.get(CONF_MIN_STATE_DURATION)
    state_class = validated_data.get(CONF_STATE_CLASS)

    history_stats = HistoryStats(
        hass,
        entity_id,
        entity_states,
        Template(start, hass) if start else None,
        Template(end, hass) if end else None,
        timedelta(**duration) if duration else None,
        timedelta(**min_state_duration) if min_state_duration else timedelta(0),
        True,
    )
    coordinator = HistoryStatsUpdateCoordinator(hass, history_stats, None, name, True)
    await coordinator.async_refresh()
    preview_entity = HistoryStatsSensor(
        hass,
        coordinator=coordinator,
        sensor_type=sensor_type,
        name=name,
        unique_id=None,
        source_entity_id=entity_id,
        state_class=state_class,
    )
    preview_entity.hass = hass

    connection.send_result(msg["id"])
    cancel_listener = coordinator.async_setup_state_listener()
    cancel_preview = await preview_entity.async_start_preview(async_preview_updated)

    def unsub() -> None:
        cancel_listener()
        cancel_preview()

    connection.subscriptions[msg["id"]] = unsub