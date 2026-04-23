async def test_subscribe_log_updates(
    hass: HomeAssistant, integration, client, hass_ws_client: WebSocketGenerator
) -> None:
    """Test the subscribe_log_updates websocket command."""
    entry = integration
    ws_client = await hass_ws_client(hass)

    client.async_send_command.return_value = {}

    await ws_client.send_json(
        {ID: 1, TYPE: "zwave_js/subscribe_log_updates", ENTRY_ID: entry.entry_id}
    )

    msg = await ws_client.receive_json()
    assert msg["success"]

    event = Event(
        type="logging",
        data={
            "source": "driver",
            "event": "logging",
            "message": "test",
            "formattedMessage": "test",
            "direction": ">",
            "level": "debug",
            "primaryTags": "tag",
            "secondaryTags": "tag2",
            "secondaryTagPadding": 0,
            "multiline": False,
            "timestamp": "time",
            "label": "label",
            "context": {"source": "config"},
        },
    )
    client.driver.receive_event(event)

    msg = await ws_client.receive_json()
    assert msg["event"] == {
        "type": "log_message",
        "log_message": {
            "message": ["test"],
            "level": "debug",
            "primary_tags": "tag",
            "timestamp": "time",
        },
    }

    event = Event(
        type="log config updated",
        data={
            "source": "driver",
            "event": "log config updated",
            "config": {
                "enabled": False,
                "level": "error",
                "logToFile": True,
                "filename": "test",
                "forceConsole": True,
            },
        },
    )
    client.driver.receive_event(event)

    msg = await ws_client.receive_json()
    assert msg["event"] == {
        "type": "log_config",
        "log_config": {
            "enabled": False,
            "level": "error",
            "log_to_file": True,
            "filename": "test",
            "force_console": True,
        },
    }

    # Test FailedZWaveCommand is caught
    client.async_start_listening_logs.side_effect = FailedZWaveCommand(
        "failed_command", 1, "error message"
    )
    await ws_client.send_json(
        {
            ID: 2,
            TYPE: "zwave_js/subscribe_log_updates",
            ENTRY_ID: entry.entry_id,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == "zwave_error"
    assert msg["error"]["message"] == "zwave_error: Z-Wave error 1 - error message"

    # Test sending command with not loaded entry fails
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    await ws_client.send_json(
        {ID: 3, TYPE: "zwave_js/subscribe_log_updates", ENTRY_ID: entry.entry_id}
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED