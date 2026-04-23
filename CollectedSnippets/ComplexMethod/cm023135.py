async def test_update_log_config(
    hass: HomeAssistant, client, integration, hass_ws_client: WebSocketGenerator
) -> None:
    """Test that update_log_config WS API call and schema validation works."""
    entry = integration
    ws_client = await hass_ws_client(hass)

    # Test we can set log level
    client.async_send_command.return_value = {"success": True}
    await ws_client.send_json(
        {
            ID: 1,
            TYPE: "zwave_js/update_log_config",
            ENTRY_ID: entry.entry_id,
            CONFIG: {LEVEL: "Error"},
        }
    )
    msg = await ws_client.receive_json()
    assert msg["success"]

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "driver.update_log_config"
    assert args["config"] == {"level": "error"}

    client.async_send_command.reset_mock()

    # Test we can set logToFile to True
    client.async_send_command.return_value = {"success": True}
    await ws_client.send_json(
        {
            ID: 2,
            TYPE: "zwave_js/update_log_config",
            ENTRY_ID: entry.entry_id,
            CONFIG: {LOG_TO_FILE: True, FILENAME: "/test"},
        }
    )
    msg = await ws_client.receive_json()
    assert msg["success"]

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "driver.update_log_config"
    assert args["config"] == {"logToFile": True, "filename": "/test"}

    client.async_send_command.reset_mock()

    # Test all parameters
    client.async_send_command.return_value = {"success": True}
    await ws_client.send_json(
        {
            ID: 3,
            TYPE: "zwave_js/update_log_config",
            ENTRY_ID: entry.entry_id,
            CONFIG: {
                LEVEL: "Error",
                LOG_TO_FILE: True,
                FILENAME: "/test",
                FORCE_CONSOLE: True,
                ENABLED: True,
            },
        }
    )
    msg = await ws_client.receive_json()
    assert msg["success"]

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "driver.update_log_config"
    assert args["config"] == {
        "level": "error",
        "logToFile": True,
        "filename": "/test",
        "forceConsole": True,
        "enabled": True,
    }

    client.async_send_command.reset_mock()

    # Test error when setting unrecognized log level
    await ws_client.send_json(
        {
            ID: 4,
            TYPE: "zwave_js/update_log_config",
            ENTRY_ID: entry.entry_id,
            CONFIG: {LEVEL: "bad_log_level"},
        }
    )
    msg = await ws_client.receive_json()
    assert not msg["success"]
    assert "error" in msg and msg["error"]["code"] == "invalid_format"

    # Test error without service data
    await ws_client.send_json(
        {
            ID: 5,
            TYPE: "zwave_js/update_log_config",
            ENTRY_ID: entry.entry_id,
            CONFIG: {},
        }
    )
    msg = await ws_client.receive_json()
    assert not msg["success"]
    assert "error" in msg and "must contain at least one of" in msg["error"]["message"]

    # Test error if we set logToFile to True without providing filename
    await ws_client.send_json(
        {
            ID: 6,
            TYPE: "zwave_js/update_log_config",
            ENTRY_ID: entry.entry_id,
            CONFIG: {LOG_TO_FILE: True},
        }
    )
    msg = await ws_client.receive_json()
    assert not msg["success"]
    assert (
        "error" in msg
        and "must be provided if logging to file" in msg["error"]["message"]
    )

    # Test FailedZWaveCommand is caught
    with patch(
        "zwave_js_server.model.driver.Driver.async_update_log_config",
        side_effect=FailedZWaveCommand("failed_command", 1, "error message"),
    ):
        await ws_client.send_json(
            {
                ID: 7,
                TYPE: "zwave_js/update_log_config",
                ENTRY_ID: entry.entry_id,
                CONFIG: {LEVEL: "Error"},
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
            ID: 8,
            TYPE: "zwave_js/update_log_config",
            ENTRY_ID: entry.entry_id,
            CONFIG: {LEVEL: "Error"},
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED