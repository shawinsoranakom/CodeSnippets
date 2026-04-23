async def test_subscribe_s2_inclusion(
    hass: HomeAssistant, integration, client, hass_ws_client: WebSocketGenerator
) -> None:
    """Test the subscribe_s2_inclusion websocket command."""
    entry = integration
    ws_client = await hass_ws_client(hass)

    await ws_client.send_json_auto_id(
        {
            TYPE: "zwave_js/subscribe_s2_inclusion",
            ENTRY_ID: entry.entry_id,
        }
    )

    msg = await ws_client.receive_json()
    assert msg["success"]
    assert msg["result"] is None

    # Test receiving requested grant event
    event = Event(
        type="grant security classes",
        data={
            "source": "controller",
            "event": "grant security classes",
            "requested": {
                "securityClasses": [SecurityClass.S2_UNAUTHENTICATED],
                "clientSideAuth": False,
            },
        },
    )
    client.driver.receive_event(event)

    # Test receiving DSK request event
    event = Event(
        type="validate dsk and enter pin",
        data={
            "source": "controller",
            "event": "validate dsk and enter pin",
            "dsk": "test_dsk",
        },
    )
    client.driver.receive_event(event)

    msg = await ws_client.receive_json()
    assert msg["event"] == {
        "event": "validate dsk and enter pin",
        "dsk": "test_dsk",
    }

    # Test sending command with not loaded entry fails
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    await ws_client.send_json_auto_id(
        {
            TYPE: "zwave_js/subscribe_s2_inclusion",
            ENTRY_ID: entry.entry_id,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED

    # Test invalid config entry id
    await ws_client.send_json_auto_id(
        {
            TYPE: "zwave_js/subscribe_s2_inclusion",
            ENTRY_ID: "INVALID",
        }
    )
    msg = await ws_client.receive_json()
    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_FOUND