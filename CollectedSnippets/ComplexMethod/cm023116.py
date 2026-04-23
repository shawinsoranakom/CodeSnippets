async def test_unprovision_smart_start_node(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    integration,
    client,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test unprovision_smart_start_node websocket command."""
    entry = integration
    ws_client = await hass_ws_client(hass)

    client.async_send_command.return_value = {}

    # Test node ID as input
    await ws_client.send_json_auto_id(
        {
            TYPE: "zwave_js/unprovision_smart_start_node",
            ENTRY_ID: entry.entry_id,
            NODE_ID: 1,
        }
    )

    msg = await ws_client.receive_json()
    assert msg["success"]

    assert len(client.async_send_command.call_args_list) == 2
    assert client.async_send_command.call_args_list[0][0][0] == {
        "command": "controller.get_provisioning_entry",
        "dskOrNodeId": 1,
    }
    assert client.async_send_command.call_args_list[1][0][0] == {
        "command": "controller.unprovision_smart_start_node",
        "dskOrNodeId": 1,
    }

    client.async_send_command.reset_mock()
    client.async_send_command.return_value = {}

    # Test DSK as input
    await ws_client.send_json_auto_id(
        {
            TYPE: "zwave_js/unprovision_smart_start_node",
            ENTRY_ID: entry.entry_id,
            DSK: "test",
        }
    )

    msg = await ws_client.receive_json()
    assert msg["success"]

    assert len(client.async_send_command.call_args_list) == 2
    assert client.async_send_command.call_args_list[0][0][0] == {
        "command": "controller.get_provisioning_entry",
        "dskOrNodeId": "test",
    }
    assert client.async_send_command.call_args_list[1][0][0] == {
        "command": "controller.unprovision_smart_start_node",
        "dskOrNodeId": "test",
    }

    client.async_send_command.reset_mock()
    client.async_send_command.return_value = {}

    # Test not including DSK or node ID as input fails
    await ws_client.send_json_auto_id(
        {
            TYPE: "zwave_js/unprovision_smart_start_node",
            ENTRY_ID: entry.entry_id,
        }
    )

    msg = await ws_client.receive_json()
    assert not msg["success"]

    assert len(client.async_send_command.call_args_list) == 0

    # Test with pre provisioned device
    # Create device registry entry for mock node
    device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, "provision_test"), ("other_domain", "test")},
        name="Node 67",
    )
    provisioning_entry = ProvisioningEntry.from_dict(
        {
            "dsk": "test",
            "securityClasses": [SecurityClass.S2_UNAUTHENTICATED],
            "device_id": device.id,
        }
    )
    with patch.object(
        client.driver.controller,
        "async_get_provisioning_entry",
        return_value=provisioning_entry,
    ):
        # Don't remove the device if it has additional identifiers
        await ws_client.send_json_auto_id(
            {
                TYPE: "zwave_js/unprovision_smart_start_node",
                ENTRY_ID: entry.entry_id,
                DSK: "test",
            }
        )
        msg = await ws_client.receive_json()
        assert msg["success"]

        assert len(client.async_send_command.call_args_list) == 1
        assert client.async_send_command.call_args[0][0] == {
            "command": "controller.unprovision_smart_start_node",
            "dskOrNodeId": "test",
        }

        device = device_registry.async_get(device.id)
        assert device is not None

        client.async_send_command.reset_mock()

        # Remove the device if it doesn't have additional identifiers
        device_registry.async_update_device(
            device.id, new_identifiers={(DOMAIN, "provision_test")}
        )
        await ws_client.send_json_auto_id(
            {
                TYPE: "zwave_js/unprovision_smart_start_node",
                ENTRY_ID: entry.entry_id,
                DSK: "test",
            }
        )
        msg = await ws_client.receive_json()
        assert msg["success"]

        assert len(client.async_send_command.call_args_list) == 1
        assert client.async_send_command.call_args[0][0] == {
            "command": "controller.unprovision_smart_start_node",
            "dskOrNodeId": "test",
        }

        # Verify device was removed from device registry
        device = device_registry.async_get(device.id)
        assert device is None

    # Test FailedZWaveCommand is caught
    with patch(
        f"{CONTROLLER_PATCH_PREFIX}.async_unprovision_smart_start_node",
        side_effect=FailedZWaveCommand("failed_command", 1, "error message"),
    ):
        await ws_client.send_json_auto_id(
            {
                TYPE: "zwave_js/unprovision_smart_start_node",
                ENTRY_ID: entry.entry_id,
                DSK: "test",
            }
        )
        msg = await ws_client.receive_json()

        assert not msg["success"]
        assert msg["error"]["code"] == "zwave_error"
        assert msg["error"]["message"] == "zwave_error: Z-Wave error 1 - error message"

    # Test sending command with not loaded entry fails
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    await ws_client.send_json_auto_id(
        {
            TYPE: "zwave_js/unprovision_smart_start_node",
            ENTRY_ID: entry.entry_id,
            DSK: "test",
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED