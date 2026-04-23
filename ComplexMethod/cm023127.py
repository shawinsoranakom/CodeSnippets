async def test_refresh_node_info(
    hass: HomeAssistant,
    client,
    multisensor_6,
    integration,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test that the refresh_node_info WS API call works."""
    entry = integration
    ws_client = await hass_ws_client(hass)

    device = get_device(hass, multisensor_6)

    client.async_send_command_no_wait.return_value = None
    await ws_client.send_json(
        {
            ID: 1,
            TYPE: "zwave_js/refresh_node_info",
            DEVICE_ID: device.id,
        }
    )
    msg = await ws_client.receive_json()
    assert msg["success"]

    assert len(client.async_send_command_no_wait.call_args_list) == 1
    args = client.async_send_command_no_wait.call_args[0][0]
    assert args["command"] == "node.refresh_info"
    assert args["nodeId"] == 52

    event = Event(
        type="interview started",
        data={"source": "node", "event": "interview started", "nodeId": 52},
    )
    client.driver.receive_event(event)

    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "interview started"

    event = Event(
        type="interview stage completed",
        data={
            "source": "node",
            "event": "interview stage completed",
            "stageName": "NodeInfo",
            "nodeId": 52,
        },
    )
    client.driver.receive_event(event)

    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "interview stage completed"
    assert msg["event"]["stage"] == "NodeInfo"

    event = Event(
        type="interview completed",
        data={"source": "node", "event": "interview completed", "nodeId": 52},
    )
    client.driver.receive_event(event)

    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "interview completed"

    event = Event(
        type="interview failed",
        data={
            "source": "node",
            "event": "interview failed",
            "nodeId": 52,
            "args": {
                "errorMessage": "error",
                "isFinal": True,
            },
        },
    )
    client.driver.receive_event(event)

    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "interview failed"

    client.async_send_command_no_wait.reset_mock()

    # Test getting non-existent node fails
    await ws_client.send_json(
        {
            ID: 2,
            TYPE: "zwave_js/refresh_node_info",
            DEVICE_ID: "fake_device",
        }
    )
    msg = await ws_client.receive_json()
    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_FOUND

    # Test FailedZWaveCommand is caught
    with patch(
        "zwave_js_server.model.node.Node.async_refresh_info",
        side_effect=FailedZWaveCommand("failed_command", 1, "error message"),
    ):
        await ws_client.send_json(
            {
                ID: 3,
                TYPE: "zwave_js/refresh_node_info",
                DEVICE_ID: device.id,
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
        {
            ID: 4,
            TYPE: "zwave_js/refresh_node_info",
            DEVICE_ID: device.id,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED