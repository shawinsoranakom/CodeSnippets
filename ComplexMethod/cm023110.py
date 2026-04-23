async def test_subscribe_node_status(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    multisensor_6_state,
    client,
    integration,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test the subscribe node status websocket command."""
    entry = integration
    ws_client = await hass_ws_client(hass)
    node_data = deepcopy(multisensor_6_state)  # Copy to allow modification in tests.
    node = Node(client, node_data)
    node.data["ready"] = False
    driver = client.driver
    driver.controller.nodes[node.node_id] = node

    device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={get_device_id(driver, node)}
    )

    await ws_client.send_json(
        {
            ID: 3,
            TYPE: "zwave_js/subscribe_node_status",
            DEVICE_ID: device.id,
        }
    )

    msg = await ws_client.receive_json()
    assert msg["success"]

    new_node_data = deepcopy(multisensor_6_state)
    new_node_data["ready"] = True

    event = Event(
        "ready",
        {
            "source": "node",
            "event": "ready",
            "nodeId": node.node_id,
            "nodeState": new_node_data,
        },
    )
    node.receive_event(event)
    await hass.async_block_till_done()

    msg = await ws_client.receive_json()

    assert msg["event"]["event"] == "ready"
    assert msg["event"]["status"] == 1
    assert msg["event"]["ready"]

    event = Event(
        "wake up",
        {
            "source": "node",
            "event": "wake up",
            "nodeId": node.node_id,
        },
    )
    node.receive_event(event)
    await hass.async_block_till_done()

    msg = await ws_client.receive_json()

    assert msg["event"]["event"] == "wake up"
    assert msg["event"]["status"] == 2
    assert msg["event"]["ready"]