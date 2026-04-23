async def test_provision_smart_start_node(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    integration,
    client,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test provision_smart_start_node websocket command."""
    entry = integration
    ws_client = await hass_ws_client(hass)

    client.async_send_command.return_value = {"success": True}

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
        "name": "test",
    }

    # Test QR provisioning information
    await ws_client.send_json(
        {
            ID: 3,
            TYPE: "zwave_js/provision_smart_start_node",
            ENTRY_ID: entry.entry_id,
            QR_PROVISIONING_INFORMATION: valid_qr_info,
        }
    )

    msg = await ws_client.receive_json()
    assert msg["success"]

    assert len(client.async_send_command.call_args_list) == 1
    assert client.async_send_command.call_args[0][0] == {
        "command": "controller.provision_smart_start_node",
        "entry": ProvisioningEntry(
            dsk="test",
            security_classes=[SecurityClass.S2_UNAUTHENTICATED],
            additional_properties={"name": "test"},
        ).to_dict(),
    }

    client.async_send_command.reset_mock()
    client.async_send_command.return_value = {"success": True}

    # Test QR provisioning information with device name and area
    await ws_client.send_json(
        {
            ID: 4,
            TYPE: "zwave_js/provision_smart_start_node",
            ENTRY_ID: entry.entry_id,
            QR_PROVISIONING_INFORMATION: {
                **valid_qr_info,
            },
            PROTOCOL: Protocols.ZWAVE_LONG_RANGE,
            DEVICE_NAME: "test_name",
            AREA_ID: "test_area",
        }
    )
    msg = await ws_client.receive_json()
    assert msg["success"]

    # verify a device was created
    device = device_registry.async_get_device(
        identifiers={(DOMAIN, "provision_test")},
    )
    assert device is not None
    assert device.name == "test_name"
    assert device.area_id == "test_area"

    assert len(client.async_send_command.call_args_list) == 2
    assert client.async_send_command.call_args_list[0][0][0] == {
        "command": "config_manager.lookup_device",
        "manufacturerId": 1,
        "productType": 1,
        "productId": 1,
    }
    assert client.async_send_command.call_args_list[1][0][0] == {
        "command": "controller.provision_smart_start_node",
        "entry": ProvisioningEntry(
            dsk="test",
            security_classes=[SecurityClass.S2_UNAUTHENTICATED],
            protocol=Protocols.ZWAVE_LONG_RANGE,
            additional_properties={
                "name": "test",
                "device_id": device.id,
            },
        ).to_dict(),
    }

    # Test QR provisioning information with S2 version throws error
    await ws_client.send_json(
        {
            ID: 5,
            TYPE: "zwave_js/provision_smart_start_node",
            ENTRY_ID: entry.entry_id,
            QR_PROVISIONING_INFORMATION: {
                VERSION: 0,
                SECURITY_CLASSES: [0],
                DSK: "test",
                GENERIC_DEVICE_CLASS: 1,
                SPECIFIC_DEVICE_CLASS: 1,
                INSTALLER_ICON_TYPE: 1,
                MANUFACTURER_ID: 1,
                PRODUCT_TYPE: 1,
                PRODUCT_ID: 1,
                APPLICATION_VERSION: "test",
            },
        }
    )

    msg = await ws_client.receive_json()
    assert not msg["success"]

    client.async_send_command.reset_mock()
    client.async_send_command.return_value = {"success": True}
    assert len(client.async_send_command.call_args_list) == 0

    # Test no provisioning parameter provided causes failure
    await ws_client.send_json(
        {
            ID: 6,
            TYPE: "zwave_js/provision_smart_start_node",
            ENTRY_ID: entry.entry_id,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]

    # Test FailedZWaveCommand is caught
    with patch(
        f"{CONTROLLER_PATCH_PREFIX}.async_provision_smart_start_node",
        side_effect=FailedZWaveCommand("failed_command", 1, "error message"),
    ):
        await ws_client.send_json(
            {
                ID: 7,
                TYPE: "zwave_js/provision_smart_start_node",
                ENTRY_ID: entry.entry_id,
                QR_PROVISIONING_INFORMATION: valid_qr_info,
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
            ID: 8,
            TYPE: "zwave_js/provision_smart_start_node",
            ENTRY_ID: entry.entry_id,
            QR_PROVISIONING_INFORMATION: valid_qr_info,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED