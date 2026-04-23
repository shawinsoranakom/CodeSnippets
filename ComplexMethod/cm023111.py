async def test_node_status(
    hass: HomeAssistant, multisensor_6, integration, hass_ws_client: WebSocketGenerator
) -> None:
    """Test the node status websocket command."""
    entry = integration
    ws_client = await hass_ws_client(hass)

    node = multisensor_6
    device = get_device(hass, node)
    await ws_client.send_json(
        {
            ID: 3,
            TYPE: "zwave_js/node_status",
            DEVICE_ID: device.id,
        }
    )
    msg = await ws_client.receive_json()
    result = msg["result"]

    assert result[NODE_ID] == 52
    assert result["ready"]
    assert result["is_routing"]
    assert not result["is_secure"]
    assert result["status"] == 1
    assert result["zwave_plus_version"] == 1
    assert result["highest_security_class"] == SecurityClass.S0_LEGACY
    assert not result["is_controller_node"]
    assert not result["has_firmware_update_cc"]

    # Test getting non-existent node fails
    await ws_client.send_json(
        {
            ID: 4,
            TYPE: "zwave_js/node_status",
            DEVICE_ID: "fake_device",
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
            ID: 5,
            TYPE: "zwave_js/node_status",
            DEVICE_ID: device.id,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED