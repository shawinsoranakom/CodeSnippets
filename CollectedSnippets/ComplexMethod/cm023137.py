async def test_data_collection(
    hass: HomeAssistant, client, integration, hass_ws_client: WebSocketGenerator
) -> None:
    """Test that the data collection WS API commands work."""
    entry = integration
    ws_client = await hass_ws_client(hass)

    client.async_send_command.return_value = {"statisticsEnabled": False}
    await ws_client.send_json(
        {
            ID: 1,
            TYPE: "zwave_js/data_collection_status",
            ENTRY_ID: entry.entry_id,
        }
    )
    msg = await ws_client.receive_json()
    result = msg["result"]
    assert result == {"opted_in": None, "enabled": False}

    assert len(client.async_send_command.call_args_list) == 1
    assert client.async_send_command.call_args[0][0] == {
        "command": "driver.is_statistics_enabled"
    }

    assert CONF_DATA_COLLECTION_OPTED_IN not in entry.data

    client.async_send_command.reset_mock()

    client.async_send_command.return_value = {}
    await ws_client.send_json(
        {
            ID: 2,
            TYPE: "zwave_js/update_data_collection_preference",
            ENTRY_ID: entry.entry_id,
            OPTED_IN: True,
        }
    )
    msg = await ws_client.receive_json()
    result = msg["result"]
    assert result is None

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args_list[0][0][0]
    assert args["command"] == "driver.enable_statistics"
    assert args["applicationName"] == "Home Assistant"

    client.async_send_command.reset_mock()

    client.async_send_command.return_value = {}
    await ws_client.send_json(
        {
            ID: 3,
            TYPE: "zwave_js/update_data_collection_preference",
            ENTRY_ID: entry.entry_id,
            OPTED_IN: False,
        }
    )
    msg = await ws_client.receive_json()
    result = msg["result"]
    assert result is None

    assert len(client.async_send_command.call_args_list) == 1
    assert client.async_send_command.call_args[0][0] == {
        "command": "driver.disable_statistics"
    }
    assert not entry.data[CONF_DATA_COLLECTION_OPTED_IN]

    client.async_send_command.reset_mock()

    # Test FailedZWaveCommand is caught
    with patch(
        "zwave_js_server.model.driver.Driver.async_is_statistics_enabled",
        side_effect=FailedZWaveCommand("failed_command", 1, "error message"),
    ):
        await ws_client.send_json(
            {
                ID: 4,
                TYPE: "zwave_js/data_collection_status",
                ENTRY_ID: entry.entry_id,
            }
        )
        msg = await ws_client.receive_json()

        assert not msg["success"]
        assert msg["error"]["code"] == "zwave_error"
        assert msg["error"]["message"] == "zwave_error: Z-Wave error 1 - error message"

    # Test FailedZWaveCommand is caught
    with patch(
        "zwave_js_server.model.driver.Driver.async_enable_statistics",
        side_effect=FailedZWaveCommand("failed_command", 1, "error message"),
    ):
        await ws_client.send_json(
            {
                ID: 5,
                TYPE: "zwave_js/update_data_collection_preference",
                ENTRY_ID: entry.entry_id,
                OPTED_IN: True,
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
            ID: 6,
            TYPE: "zwave_js/data_collection_status",
            ENTRY_ID: entry.entry_id,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED

    await ws_client.send_json(
        {
            ID: 7,
            TYPE: "zwave_js/update_data_collection_preference",
            ENTRY_ID: entry.entry_id,
            OPTED_IN: True,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED