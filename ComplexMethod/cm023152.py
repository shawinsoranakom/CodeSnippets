async def test_lookup_device(
    hass: HomeAssistant,
    integration: MockConfigEntry,
    client: MagicMock,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test lookup_device websocket command."""
    entry = integration
    ws_client = await hass_ws_client(hass)

    # Create mock device response
    mock_device = MagicMock()
    mock_device.to_dict.return_value = {
        "manufacturer": "Test Manufacturer",
        "label": "Test Device",
        "description": "Test Device Description",
        "devices": [{"productType": 1, "productId": 2}],
        "firmwareVersion": {"min": "1.0", "max": "2.0"},
    }

    # Test successful lookup
    client.driver.config_manager.lookup_device = AsyncMock(return_value=mock_device)

    await ws_client.send_json_auto_id(
        {
            TYPE: "zwave_js/lookup_device",
            ENTRY_ID: entry.entry_id,
            MANUFACTURER_ID: 1,
            PRODUCT_TYPE: 2,
            PRODUCT_ID: 3,
            APPLICATION_VERSION: "1.5",
        }
    )
    msg = await ws_client.receive_json()

    assert msg["success"]
    assert msg["result"] == mock_device.to_dict.return_value

    client.driver.config_manager.lookup_device.assert_called_once_with(1, 2, 3, "1.5")

    # Reset mock
    client.driver.config_manager.lookup_device.reset_mock()

    # Test lookup without optional application_version
    await ws_client.send_json_auto_id(
        {
            TYPE: "zwave_js/lookup_device",
            ENTRY_ID: entry.entry_id,
            MANUFACTURER_ID: 4,
            PRODUCT_TYPE: 5,
            PRODUCT_ID: 6,
        }
    )
    msg = await ws_client.receive_json()

    assert msg["success"]
    assert msg["result"] == mock_device.to_dict.return_value

    client.driver.config_manager.lookup_device.assert_called_once_with(4, 5, 6, None)

    # Test device not found
    with patch.object(
        client.driver.config_manager,
        "lookup_device",
        return_value=None,
    ):
        await ws_client.send_json_auto_id(
            {
                TYPE: "zwave_js/lookup_device",
                ENTRY_ID: entry.entry_id,
                MANUFACTURER_ID: 99,
                PRODUCT_TYPE: 99,
                PRODUCT_ID: 99,
                APPLICATION_VERSION: "9.9",
            }
        )
        msg = await ws_client.receive_json()

        assert not msg["success"]
        assert msg["error"]["code"] == ERR_NOT_FOUND
        assert msg["error"]["message"] == "Device not found"

    # Test sending command with improper entry ID fails
    await ws_client.send_json_auto_id(
        {
            TYPE: "zwave_js/lookup_device",
            ENTRY_ID: "invalid_entry_id",
            MANUFACTURER_ID: 1,
            PRODUCT_TYPE: 1,
            PRODUCT_ID: 1,
            APPLICATION_VERSION: "1.0",
        }
    )
    msg = await ws_client.receive_json()
    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_FOUND
    assert msg["error"]["message"] == "Config entry invalid_entry_id not found"

    # Test FailedCommand exception
    error_message = "Failed to execute lookup_device command"
    with patch.object(
        client.driver.config_manager,
        "lookup_device",
        side_effect=FailedCommand("lookup_device", error_message),
    ):
        # Send the subscription request
        await ws_client.send_json_auto_id(
            {
                TYPE: "zwave_js/lookup_device",
                ENTRY_ID: entry.entry_id,
                MANUFACTURER_ID: 1,
                PRODUCT_TYPE: 2,
                PRODUCT_ID: 3,
                APPLICATION_VERSION: "1.0",
            }
        )

        # Verify error response
        msg = await ws_client.receive_json()
        assert not msg["success"]
        assert msg["error"]["code"] == error_message
        assert msg["error"]["message"] == f"Command failed: {error_message}"