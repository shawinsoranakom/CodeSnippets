async def ws_subscribe_scanner_details(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Handle subscribe scanner details websocket command."""
    ws_msg_id = msg["id"]
    config_entry_id = msg.get("config_entry_id")
    source = _async_get_source_from_config_entry(
        hass, connection, ws_msg_id, config_entry_id, validate_source=False
    )
    if config_entry_id and source is None:
        return  # Error already sent by helper

    def _async_event_message(message: dict[str, Any]) -> None:
        connection.send_message(
            json_bytes(websocket_api.event_message(ws_msg_id, message))
        )

    def _async_registration_changed(registration: HaScannerRegistration) -> None:
        added_event = HaScannerRegistrationEvent.ADDED
        event_type = "add" if registration.event == added_event else "remove"
        _async_event_message({event_type: [registration.scanner.details]})

    manager = _get_manager(hass)
    connection.subscriptions[ws_msg_id] = (
        manager.async_register_scanner_registration_callback(
            _async_registration_changed, source
        )
    )
    connection.send_message(json_bytes(websocket_api.result_message(ws_msg_id)))
    if (scanners := manager.async_current_scanners()) and (
        matching_scanners := [
            scanner.details
            for scanner in scanners
            if source is None or scanner.source == source
        ]
    ):
        _async_event_message({"add": matching_scanners})