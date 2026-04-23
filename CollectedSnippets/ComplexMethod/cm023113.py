async def test_node_alerts(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    wallmote_central_scene,
    integration,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test the node comments websocket command."""
    entry = integration
    ws_client = await hass_ws_client(hass)

    device = device_registry.async_get_device(identifiers={(DOMAIN, "3245146787-35")})
    assert device

    await ws_client.send_json_auto_id(
        {
            TYPE: "zwave_js/node_alerts",
            DEVICE_ID: device.id,
        }
    )
    msg = await ws_client.receive_json()
    result = msg["result"]
    assert result["comments"] == [{"level": "info", "text": "test"}]
    assert result["is_embedded"]

    # Test with node in interview
    with patch("zwave_js_server.model.node.Node.in_interview", return_value=True):
        await ws_client.send_json_auto_id(
            {
                TYPE: "zwave_js/node_alerts",
                DEVICE_ID: device.id,
            }
        )
        msg = await ws_client.receive_json()
        assert msg["success"]
        assert len(msg["result"]["comments"]) == 2
        assert msg["result"]["comments"][1] == {
            "level": "warning",
            "text": "This device is currently being interviewed and may not be fully operational.",
        }

    # Test with provisioned device
    valid_qr_info = {
        VERSION: 1,
        SECURITY_CLASSES: [0],
        DSK: "test",
        GENERIC_DEVICE_CLASS: 1,
        SPECIFIC_DEVICE_CLASS: 1,
        INSTALLER_ICON_TYPE: 1,
        MANUFACTURER_ID: 1,
        PRODUCT_TYPE: 1,
        PRODUCT_ID: 1,
        APPLICATION_VERSION: "test",
    }

    # Test QR provisioning information
    await ws_client.send_json_auto_id(
        {
            TYPE: "zwave_js/provision_smart_start_node",
            ENTRY_ID: entry.entry_id,
            QR_PROVISIONING_INFORMATION: valid_qr_info,
            DEVICE_NAME: "test",
        }
    )
    msg = await ws_client.receive_json()
    assert msg["success"]

    with patch(
        f"{CONTROLLER_PATCH_PREFIX}.async_get_provisioning_entries",
        return_value=[
            ProvisioningEntry.from_dict({**valid_qr_info, "device_id": msg["result"]})
        ],
    ):
        await ws_client.send_json_auto_id(
            {
                TYPE: "zwave_js/node_alerts",
                DEVICE_ID: msg["result"],
            }
        )
        msg = await ws_client.receive_json()
        assert msg["success"]
        assert msg["result"]["comments"] == [
            {
                "level": "info",
                "text": "This device has been provisioned but is not yet included in the network.",
            }
        ]

    # Test missing node with no provisioning entry
    device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, "3245146787-12")},
    )
    assert device
    await ws_client.send_json_auto_id(
        {
            TYPE: "zwave_js/node_alerts",
            DEVICE_ID: device.id,
        }
    )
    msg = await ws_client.receive_json()
    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_FOUND

    # Test integration not loaded error - need to unload the integration
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    await ws_client.send_json_auto_id(
        {
            TYPE: "zwave_js/node_alerts",
            DEVICE_ID: device.id,
        }
    )
    msg = await ws_client.receive_json()
    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED