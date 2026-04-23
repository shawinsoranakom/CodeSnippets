async def test_network_status(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    multisensor_6,
    controller_state,
    client,
    integration,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test the network status websocket command."""
    entry = integration
    ws_client = await hass_ws_client(hass)
    client.server_logging_enabled = False

    # Try API call with entry ID
    with patch(
        f"{CONTROLLER_PATCH_PREFIX}.async_get_state",
        return_value=controller_state["controller"],
    ):
        await ws_client.send_json(
            {
                ID: 1,
                TYPE: "zwave_js/network_status",
                ENTRY_ID: entry.entry_id,
            }
        )
        msg = await ws_client.receive_json()
        result = msg["result"]

    assert result["client"]["ws_server_url"] == "ws://test:3000/zjs"
    assert result["client"]["server_version"] == "1.0.0"
    assert not result["client"]["server_logging_enabled"]
    assert result["controller"]["inclusion_state"] == InclusionState.IDLE
    assert result["controller"]["supports_long_range"]

    # Try API call with device ID
    device = device_registry.async_get_device(
        identifiers={(DOMAIN, "3245146787-52")},
    )
    assert device
    with patch(
        f"{CONTROLLER_PATCH_PREFIX}.async_get_state",
        return_value=controller_state["controller"],
    ):
        await ws_client.send_json(
            {
                ID: 2,
                TYPE: "zwave_js/network_status",
                DEVICE_ID: device.id,
            }
        )
        msg = await ws_client.receive_json()
        result = msg["result"]

    assert result["client"]["ws_server_url"] == "ws://test:3000/zjs"
    assert result["client"]["server_version"] == "1.0.0"
    assert result["controller"]["inclusion_state"] == InclusionState.IDLE

    # Test sending command with invalid config entry ID fails
    await ws_client.send_json(
        {
            ID: 3,
            TYPE: "zwave_js/network_status",
            ENTRY_ID: "fake_id",
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_FOUND

    # Test sending command with invalid device ID fails
    await ws_client.send_json(
        {
            ID: 4,
            TYPE: "zwave_js/network_status",
            DEVICE_ID: "fake_id",
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_FOUND

    # Test sending command with not loaded entry fails with config entry ID
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    await ws_client.send_json(
        {
            ID: 5,
            TYPE: "zwave_js/network_status",
            ENTRY_ID: entry.entry_id,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED

    # Test sending command with not loaded entry fails with device ID
    await ws_client.send_json(
        {
            ID: 6,
            TYPE: "zwave_js/network_status",
            DEVICE_ID: device.id,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED

    # Test sending command with no device ID or entry ID fails
    await ws_client.send_json(
        {
            ID: 7,
            TYPE: "zwave_js/network_status",
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_INVALID_FORMAT