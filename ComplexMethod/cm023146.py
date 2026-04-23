async def test_hard_reset_controller(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
    device_registry: dr.DeviceRegistry,
    client: MagicMock,
    get_server_version: AsyncMock,
    integration: MockConfigEntry,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test that the hard_reset_controller WS API call works."""
    entry = integration
    ws_client = await hass_ws_client(hass)
    assert entry.unique_id == "3245146787"

    async def mock_driver_hard_reset() -> None:
        client.driver.emit(
            "driver ready", {"event": "driver ready", "source": "driver"}
        )

    client.driver.async_hard_reset = AsyncMock(side_effect=mock_driver_hard_reset)

    await ws_client.send_json_auto_id(
        {
            TYPE: "zwave_js/hard_reset_controller",
            ENTRY_ID: entry.entry_id,
        }
    )
    msg = await ws_client.receive_json()
    await hass.async_block_till_done()

    device = device_registry.async_get_device(
        identifiers={get_device_id(client.driver, client.driver.controller.nodes[1])}
    )
    assert device is not None
    assert msg["result"] == device.id
    assert msg["success"]
    assert client.driver.async_hard_reset.call_count == 1
    assert entry.unique_id == "1234"

    client.driver.async_hard_reset.reset_mock()

    # Test client connect error when getting the server version.

    get_server_version.side_effect = ClientError("Boom!")

    await ws_client.send_json_auto_id(
        {
            TYPE: "zwave_js/hard_reset_controller",
            ENTRY_ID: entry.entry_id,
        }
    )

    msg = await ws_client.receive_json()
    await hass.async_block_till_done()

    device = device_registry.async_get_device(
        identifiers={get_device_id(client.driver, client.driver.controller.nodes[1])}
    )
    assert device is not None
    assert msg["result"] == device.id
    assert msg["success"]
    assert client.driver.async_hard_reset.call_count == 1
    assert (
        "Failed to get server version, cannot update config entry "
        "unique id with new home id, after controller reset"
    ) in caplog.text

    client.driver.async_hard_reset.reset_mock()
    get_server_version.side_effect = None

    # Test sending command with driver not ready and timeout.

    async def mock_driver_hard_reset_no_driver_ready() -> None:
        pass

    client.driver.async_hard_reset.side_effect = mock_driver_hard_reset_no_driver_ready

    with patch(
        "homeassistant.components.zwave_js.helpers.DRIVER_READY_EVENT_TIMEOUT",
        new=0,
    ):
        await ws_client.send_json_auto_id(
            {
                TYPE: "zwave_js/hard_reset_controller",
                ENTRY_ID: entry.entry_id,
            }
        )
        msg = await ws_client.receive_json()
        await hass.async_block_till_done()

    device = device_registry.async_get_device(
        identifiers={get_device_id(client.driver, client.driver.controller.nodes[1])}
    )
    assert device is not None
    assert msg["result"] == device.id
    assert msg["success"]
    assert client.driver.async_hard_reset.call_count == 1

    client.driver.async_hard_reset.reset_mock()

    # Test FailedZWaveCommand is caught
    client.driver.async_hard_reset.side_effect = FailedZWaveCommand(
        "failed_command", 1, "error message"
    )

    await ws_client.send_json_auto_id(
        {
            TYPE: "zwave_js/hard_reset_controller",
            ENTRY_ID: entry.entry_id,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == "zwave_error"
    assert msg["error"]["message"] == "zwave_error: Z-Wave error 1 - error message"
    assert client.driver.async_hard_reset.call_count == 1

    client.driver.async_hard_reset.side_effect = None

    # Test sending command with not loaded entry fails
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    await ws_client.send_json_auto_id(
        {
            TYPE: "zwave_js/hard_reset_controller",
            ENTRY_ID: entry.entry_id,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED

    await ws_client.send_json_auto_id(
        {
            TYPE: "zwave_js/hard_reset_controller",
            ENTRY_ID: "INVALID",
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_FOUND