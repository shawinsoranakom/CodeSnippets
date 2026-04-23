async def test_subscribe_new_devices(
    hass: HomeAssistant,
    integration,
    client,
    hass_ws_client: WebSocketGenerator,
    multisensor_6_state,
) -> None:
    """Test the subscribe_new_devices websocket command."""
    entry = integration
    ws_client = await hass_ws_client(hass)

    await ws_client.send_json_auto_id(
        {
            TYPE: "zwave_js/subscribe_new_devices",
            ENTRY_ID: entry.entry_id,
        }
    )

    msg = await ws_client.receive_json()
    assert msg["success"]
    assert msg["result"] is None

    # Simulate a device being registered
    node = Node(client, deepcopy(multisensor_6_state))
    client.driver.controller.emit("node added", {"node": node})
    await hass.async_block_till_done()

    # Verify we receive the expected message
    msg = await ws_client.receive_json()
    assert msg["type"] == "event"
    assert msg["event"]["event"] == "device registered"
    assert msg["event"]["device"]["name"] == node.device_config.description
    assert msg["event"]["device"]["manufacturer"] == node.device_config.manufacturer
    assert msg["event"]["device"]["model"] == node.device_config.label