async def test_subscribe_controller_statistics(
    hass: HomeAssistant, integration, client, hass_ws_client: WebSocketGenerator
) -> None:
    """Test the subscribe_controller_statistics command."""
    entry = integration
    ws_client = await hass_ws_client(hass)

    await ws_client.send_json(
        {
            ID: 1,
            TYPE: "zwave_js/subscribe_controller_statistics",
            ENTRY_ID: entry.entry_id,
        }
    )

    msg = await ws_client.receive_json()
    assert msg["success"]
    assert msg["result"] is None

    msg = await ws_client.receive_json()
    assert msg["event"] == {
        "event": "statistics updated",
        "source": "controller",
        "messages_tx": 0,
        "messages_rx": 0,
        "messages_dropped_tx": 0,
        "messages_dropped_rx": 0,
        "nak": 0,
        "can": 0,
        "timeout_ack": 0,
        "timout_response": 0,
        "timeout_callback": 0,
    }

    # Fire statistics updated
    event = Event(
        "statistics updated",
        {
            "source": "controller",
            "event": "statistics updated",
            "statistics": {
                "messagesTX": 1,
                "messagesRX": 1,
                "messagesDroppedTX": 1,
                "messagesDroppedRX": 1,
                "NAK": 1,
                "CAN": 1,
                "timeoutACK": 1,
                "timeoutResponse": 1,
                "timeoutCallback": 1,
            },
        },
    )
    client.driver.controller.receive_event(event)
    msg = await ws_client.receive_json()
    assert msg["event"] == {
        "event": "statistics updated",
        "source": "controller",
        "messages_tx": 1,
        "messages_rx": 1,
        "messages_dropped_tx": 1,
        "messages_dropped_rx": 1,
        "nak": 1,
        "can": 1,
        "timeout_ack": 1,
        "timout_response": 1,
        "timeout_callback": 1,
    }

    # Test sending command with improper entry ID fails
    await ws_client.send_json(
        {
            ID: 2,
            TYPE: "zwave_js/subscribe_controller_statistics",
            ENTRY_ID: "fake_entry_id",
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_FOUND

    # Test sending command with not loaded entry fails
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    await ws_client.send_json(
        {
            ID: 3,
            TYPE: "zwave_js/subscribe_controller_statistics",
            ENTRY_ID: entry.entry_id,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED