async def test_restore_nvm(
    hass: HomeAssistant,
    integration,
    client,
    hass_ws_client: WebSocketGenerator,
    get_server_version: AsyncMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test the restore NVM websocket command."""
    entry = integration
    assert entry.unique_id == "3245146787"
    ws_client = await hass_ws_client(hass)

    # Set up mocks for the controller events
    controller = client.driver.controller

    async def mock_restore_nvm_base64(
        self, base64_data: str, options: dict[str, bool] | None = None
    ) -> None:
        controller.emit(
            "nvm convert progress",
            {"event": "nvm convert progress", "bytesRead": 100, "total": 200},
        )
        await asyncio.sleep(0)
        controller.emit(
            "nvm restore progress",
            {"event": "nvm restore progress", "bytesWritten": 150, "total": 200},
        )
        controller.data["homeId"] = 3245146787
        client.driver.emit(
            "driver ready", {"event": "driver ready", "source": "driver"}
        )

    controller.async_restore_nvm_base64 = AsyncMock(side_effect=mock_restore_nvm_base64)

    # Send the subscription request
    await ws_client.send_json_auto_id(
        {
            "type": "zwave_js/restore_nvm",
            "entry_id": integration.entry_id,
            "data": "dGVzdA==",  # base64 encoded "test"
        }
    )

    # Verify the convert progress event
    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "nvm convert progress"
    assert msg["event"]["bytesRead"] == 100
    assert msg["event"]["total"] == 200

    # Verify the restore progress event
    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "nvm restore progress"
    assert msg["event"]["bytesWritten"] == 150
    assert msg["event"]["total"] == 200

    # Verify the finished event
    msg = await ws_client.receive_json()
    assert msg["type"] == "event"
    assert msg["event"]["event"] == "finished"

    # Verify subscription success
    msg = await ws_client.receive_json()
    assert msg["type"] == "result"
    assert msg["success"] is True

    await hass.async_block_till_done()

    # Verify the restore was called
    # The first call is the relevant one for nvm restore.
    assert controller.async_restore_nvm_base64.call_count == 1
    assert controller.async_restore_nvm_base64.call_args == call(
        "dGVzdA==",
        {"preserveRoutes": False},
    )
    assert entry.unique_id == "1234"

    controller.async_restore_nvm_base64.reset_mock()

    # Test client connect error when getting the server version.

    get_server_version.side_effect = ClientError("Boom!")

    # Send the subscription request
    await ws_client.send_json_auto_id(
        {
            "type": "zwave_js/restore_nvm",
            "entry_id": entry.entry_id,
            "data": "dGVzdA==",  # base64 encoded "test"
        }
    )

    # Verify the convert progress event
    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "nvm convert progress"
    assert msg["event"]["bytesRead"] == 100
    assert msg["event"]["total"] == 200

    # Verify the restore progress event
    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "nvm restore progress"
    assert msg["event"]["bytesWritten"] == 150
    assert msg["event"]["total"] == 200

    # Verify the finished event
    msg = await ws_client.receive_json()
    assert msg["type"] == "event"
    assert msg["event"]["event"] == "finished"

    # Verify subscription success
    msg = await ws_client.receive_json()
    assert msg["type"] == "result"
    assert msg["success"] is True

    await hass.async_block_till_done()

    assert controller.async_restore_nvm_base64.call_count == 1
    assert controller.async_restore_nvm_base64.call_args == call(
        "dGVzdA==",
        {"preserveRoutes": False},
    )
    assert (
        "Failed to get server version, cannot update config entry "
        "unique id with new home id, after controller NVM restore"
    ) in caplog.text

    controller.async_restore_nvm_base64.reset_mock()
    get_server_version.side_effect = None

    # Test sending command without driver ready event causing timeout.

    async def mock_restore_nvm_without_driver_ready(
        data: bytes, options: dict[str, bool] | None = None
    ):
        controller.data["homeId"] = 3245146787

    controller.async_restore_nvm_base64.side_effect = (
        mock_restore_nvm_without_driver_ready
    )

    with patch(
        "homeassistant.components.zwave_js.helpers.DRIVER_READY_EVENT_TIMEOUT",
        new=0,
    ):
        # Send the subscription request
        await ws_client.send_json_auto_id(
            {
                "type": "zwave_js/restore_nvm",
                "entry_id": entry.entry_id,
                "data": "dGVzdA==",  # base64 encoded "test"
            }
        )

        # Verify the finished event
        msg = await ws_client.receive_json()

        assert msg["type"] == "event"
        assert msg["event"]["event"] == "finished"

        # Verify subscription success
        msg = await ws_client.receive_json()
        assert msg["type"] == "result"
        assert msg["success"] is True

        await hass.async_block_till_done()

    # Verify the restore was called
    assert controller.async_restore_nvm_base64.call_count == 1
    assert controller.async_restore_nvm_base64.call_args == call(
        "dGVzdA==",
        {"preserveRoutes": False},
    )

    controller.async_restore_nvm_base64.reset_mock()

    # Test restore failure
    controller.async_restore_nvm_base64.side_effect = FailedZWaveCommand(
        "failed_command", 1, "error message"
    )

    # Send the subscription request
    await ws_client.send_json_auto_id(
        {
            "type": "zwave_js/restore_nvm",
            "entry_id": entry.entry_id,
            "data": "dGVzdA==",  # base64 encoded "test"
        }
    )

    # Verify error response
    msg = await ws_client.receive_json()
    assert not msg["success"]
    assert msg["error"]["code"] == "zwave_error"

    await hass.async_block_till_done()

    # Verify the restore was called
    assert controller.async_restore_nvm_base64.call_count == 1
    assert controller.async_restore_nvm_base64.call_args == call(
        "dGVzdA==",
        {"preserveRoutes": False},
    )

    # Test entry_id not found
    await ws_client.send_json_auto_id(
        {
            "type": "zwave_js/restore_nvm",
            "entry_id": "invalid_entry_id",
            "data": "dGVzdA==",  # base64 encoded "test"
        }
    )
    msg = await ws_client.receive_json()
    assert not msg["success"]
    assert msg["error"]["code"] == "not_found"

    # Test config entry not loaded
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    await ws_client.send_json_auto_id(
        {
            "type": "zwave_js/restore_nvm",
            "entry_id": entry.entry_id,
            "data": "dGVzdA==",  # base64 encoded "test"
        }
    )
    msg = await ws_client.receive_json()
    assert not msg["success"]
    assert msg["error"]["code"] == "not_loaded"