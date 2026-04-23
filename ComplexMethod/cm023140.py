async def test_get_node_firmware_update_capabilities(
    hass: HomeAssistant,
    client,
    multisensor_6,
    integration,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test that the get_node_firmware_update_capabilities WS API call works."""
    entry = integration
    ws_client = await hass_ws_client(hass)
    device = get_device(hass, multisensor_6)

    client.async_send_command.return_value = {
        "capabilities": {
            "firmwareUpgradable": True,
            "firmwareTargets": [0],
            "continuesToFunction": True,
            "supportsActivation": True,
        }
    }
    await ws_client.send_json(
        {
            ID: 1,
            TYPE: "zwave_js/get_node_firmware_update_capabilities",
            DEVICE_ID: device.id,
        }
    )
    msg = await ws_client.receive_json()
    assert msg["success"]
    assert msg["result"] == {
        "firmware_upgradable": True,
        "firmware_targets": [0],
        "continues_to_function": True,
        "supports_activation": True,
    }

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.get_firmware_update_capabilities"
    assert args["nodeId"] == multisensor_6.node_id

    # Test FailedZWaveCommand is caught
    with patch(
        "zwave_js_server.model.node.Node.async_get_firmware_update_capabilities",
        side_effect=FailedZWaveCommand("failed_command", 1, "error message"),
    ):
        await ws_client.send_json(
            {
                ID: 2,
                TYPE: "zwave_js/get_node_firmware_update_capabilities",
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
            ID: 3,
            TYPE: "zwave_js/get_node_firmware_update_capabilities",
            DEVICE_ID: device.id,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED

    # Test sending command with improper device ID fails
    await ws_client.send_json(
        {
            ID: 4,
            TYPE: "zwave_js/get_node_firmware_update_capabilities",
            DEVICE_ID: "fake_device",
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_FOUND