async def test_rebuild_node_routes(
    hass: HomeAssistant,
    multisensor_6,
    integration,
    client,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test the rebuild_node_routes websocket command."""
    entry = integration
    ws_client = await hass_ws_client(hass)
    device = get_device(hass, multisensor_6)

    client.async_send_command.return_value = {"success": True}

    await ws_client.send_json(
        {
            ID: 3,
            TYPE: "zwave_js/rebuild_node_routes",
            DEVICE_ID: device.id,
        }
    )

    msg = await ws_client.receive_json()
    assert msg["success"]
    assert msg["result"]

    # Test FailedZWaveCommand is caught
    with patch(
        f"{CONTROLLER_PATCH_PREFIX}.async_rebuild_node_routes",
        side_effect=FailedZWaveCommand("failed_command", 1, "error message"),
    ):
        await ws_client.send_json(
            {
                ID: 4,
                TYPE: "zwave_js/rebuild_node_routes",
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
            ID: 5,
            TYPE: "zwave_js/rebuild_node_routes",
            DEVICE_ID: device.id,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED