async def test_subscribe_node_statistics(
    hass: HomeAssistant,
    multisensor_6,
    wallmote_central_scene,
    zen_31,
    integration,
    client,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test the subscribe_node_statistics command."""
    entry = integration
    ws_client = await hass_ws_client(hass)
    multisensor_6_device = get_device(hass, multisensor_6)
    zen_31_device = get_device(hass, zen_31)
    wallmote_central_scene_device = get_device(hass, wallmote_central_scene)

    await ws_client.send_json(
        {
            ID: 1,
            TYPE: "zwave_js/subscribe_node_statistics",
            DEVICE_ID: multisensor_6_device.id,
        }
    )

    msg = await ws_client.receive_json()
    assert msg["success"]
    assert msg["result"] is None

    msg = await ws_client.receive_json()
    assert msg["event"] == {
        "source": "node",
        "event": "statistics updated",
        "nodeId": multisensor_6.node_id,
        "commands_tx": 0,
        "commands_rx": 0,
        "commands_dropped_tx": 0,
        "commands_dropped_rx": 0,
        "timeout_response": 0,
        "rtt": None,
        "rssi": None,
        "lwr": None,
        "nlwr": None,
    }

    # Fire statistics updated
    event = Event(
        "statistics updated",
        {
            "source": "node",
            "event": "statistics updated",
            "nodeId": multisensor_6.node_id,
            "statistics": {
                "commandsTX": 1,
                "commandsRX": 2,
                "commandsDroppedTX": 3,
                "commandsDroppedRX": 4,
                "timeoutResponse": 5,
                "rtt": 6,
                "rssi": 7,
                "lwr": {
                    "protocolDataRate": 1,
                    "rssi": 1,
                    "repeaters": [wallmote_central_scene.node_id],
                    "repeaterRSSI": [1],
                    "routeFailedBetween": [
                        zen_31.node_id,
                        multisensor_6.node_id,
                    ],
                },
                "nlwr": {
                    "protocolDataRate": 2,
                    "rssi": 2,
                    "repeaters": [],
                    "repeaterRSSI": [127],
                    "routeFailedBetween": [
                        multisensor_6.node_id,
                        zen_31.node_id,
                    ],
                },
            },
        },
    )
    client.driver.controller.receive_event(event)
    msg = await ws_client.receive_json()
    assert msg["event"] == {
        "event": "statistics updated",
        "source": "node",
        "node_id": multisensor_6.node_id,
        "commands_tx": 1,
        "commands_rx": 2,
        "commands_dropped_tx": 3,
        "commands_dropped_rx": 4,
        "timeout_response": 5,
        "rtt": 6,
        "rssi": 7,
        "lwr": {
            "protocol_data_rate": 1,
            "rssi": 1,
            "repeaters": [wallmote_central_scene_device.id],
            "repeater_rssi": [1],
            "route_failed_between": [
                zen_31_device.id,
                multisensor_6_device.id,
            ],
        },
        "nlwr": {
            "protocol_data_rate": 2,
            "rssi": 2,
            "repeaters": [],
            "repeater_rssi": [127],
            "route_failed_between": [
                multisensor_6_device.id,
                zen_31_device.id,
            ],
        },
    }

    # Test sending command with improper entry ID fails
    await ws_client.send_json(
        {
            ID: 2,
            TYPE: "zwave_js/subscribe_node_statistics",
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
            ID: 4,
            TYPE: "zwave_js/subscribe_node_statistics",
            DEVICE_ID: multisensor_6_device.id,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED