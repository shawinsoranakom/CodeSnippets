async def test_add_node(
    hass: HomeAssistant,
    nortek_thermostat,
    nortek_thermostat_added_event,
    integration,
    client,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test the add_node websocket command."""
    entry = integration
    ws_client = await hass_ws_client(hass)

    client.async_send_command.return_value = {"success": True}

    # Test inclusion with no provisioning input
    await ws_client.send_json(
        {
            ID: 1,
            TYPE: "zwave_js/add_node",
            ENTRY_ID: entry.entry_id,
            INCLUSION_STRATEGY: InclusionStrategy.DEFAULT.value,
        }
    )

    msg = await ws_client.receive_json()
    assert msg["success"]

    assert len(client.async_send_command.call_args_list) == 1
    assert client.async_send_command.call_args[0][0] == {
        "command": "controller.begin_inclusion",
        "options": {"strategy": InclusionStrategy.DEFAULT},
    }

    event = Event(
        type="inclusion started",
        data={
            "source": "controller",
            "event": "inclusion started",
            "strategy": 2,
        },
    )
    client.driver.receive_event(event)

    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "inclusion started"

    event = Event(
        type="node found",
        data={
            "source": "controller",
            "event": "node found",
            "node": {
                "nodeId": 67,
            },
        },
    )
    client.driver.receive_event(event)

    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "node found"
    node_details = {
        "node_id": 67,
    }
    assert msg["event"]["node"] == node_details

    event = Event(
        type="grant security classes",
        data={
            "source": "controller",
            "event": "grant security classes",
            "requested": {"securityClasses": [0, 1, 2, 7], "clientSideAuth": False},
        },
    )
    client.driver.receive_event(event)

    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "grant security classes"
    assert msg["event"]["requested_grant"] == {
        "securityClasses": [0, 1, 2, 7],
        "clientSideAuth": False,
    }

    event = Event(
        type="validate dsk and enter pin",
        data={
            "source": "controller",
            "event": "validate dsk and enter pin",
            "dsk": "test",
        },
    )
    client.driver.receive_event(event)

    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "validate dsk and enter pin"
    assert msg["event"]["dsk"] == "test"

    client.driver.receive_event(nortek_thermostat_added_event)
    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "node added"
    node_details = {
        "node_id": 67,
        "status": 0,
        "ready": False,
        "low_security": False,
        "low_security_reason": None,
    }
    assert msg["event"]["node"] == node_details

    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "device registered"
    # Check the keys of the device item
    assert list(msg["event"]["device"]) == ["name", "id", "manufacturer", "model"]

    # Test receiving interview events
    event = Event(
        type="interview started",
        data={"source": "node", "event": "interview started", "nodeId": 67},
    )
    client.driver.receive_event(event)

    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "interview started"

    event = Event(
        type="interview stage completed",
        data={
            "source": "node",
            "event": "interview stage completed",
            "stageName": "NodeInfo",
            "nodeId": 67,
        },
    )
    client.driver.receive_event(event)

    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "interview stage completed"
    assert msg["event"]["stage"] == "NodeInfo"

    event = Event(
        type="interview completed",
        data={"source": "node", "event": "interview completed", "nodeId": 67},
    )
    client.driver.receive_event(event)

    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "interview completed"

    event = Event(
        type="interview failed",
        data={
            "source": "node",
            "event": "interview failed",
            "nodeId": 67,
            "args": {
                "errorMessage": "error",
                "isFinal": True,
            },
        },
    )
    client.driver.receive_event(event)

    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "interview failed"

    client.async_send_command.reset_mock()
    client.async_send_command.return_value = {"success": True}

    # Test S2 planned provisioning entry
    await ws_client.send_json(
        {
            ID: 2,
            TYPE: "zwave_js/add_node",
            ENTRY_ID: entry.entry_id,
            INCLUSION_STRATEGY: InclusionStrategy.SECURITY_S2.value,
            PLANNED_PROVISIONING_ENTRY: {
                DSK: "test",
                SECURITY_CLASSES: [0],
            },
        }
    )

    msg = await ws_client.receive_json()
    assert msg["success"]

    assert len(client.async_send_command.call_args_list) == 1
    assert client.async_send_command.call_args[0][0] == {
        "command": "controller.begin_inclusion",
        "options": {
            "strategy": InclusionStrategy.SECURITY_S2,
            "provisioning": ProvisioningEntry(
                "test", [SecurityClass.S2_UNAUTHENTICATED]
            ).to_dict(),
        },
    }

    client.async_send_command.reset_mock()
    client.async_send_command.return_value = {"success": True}

    # Test S2 QR provisioning information
    await ws_client.send_json(
        {
            ID: 3,
            TYPE: "zwave_js/add_node",
            ENTRY_ID: entry.entry_id,
            INCLUSION_STRATEGY: InclusionStrategy.SECURITY_S2.value,
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
    assert msg["success"]

    assert len(client.async_send_command.call_args_list) == 1
    assert client.async_send_command.call_args[0][0] == {
        "command": "controller.begin_inclusion",
        "options": {
            "strategy": InclusionStrategy.SECURITY_S2,
            "provisioning": QRProvisioningInformation(
                version=QRCodeVersion.S2,
                security_classes=[SecurityClass.S2_UNAUTHENTICATED],
                dsk="test",
                generic_device_class=1,
                specific_device_class=1,
                installer_icon_type=1,
                manufacturer_id=1,
                product_type=1,
                product_id=1,
                application_version="test",
                max_inclusion_request_interval=None,
                uuid=None,
                supported_protocols=None,
            ).to_dict(),
        },
    }

    client.async_send_command.reset_mock()
    client.async_send_command.return_value = {"success": True}

    # Test S2 QR provisioning information
    await ws_client.send_json(
        {
            ID: 4,
            TYPE: "zwave_js/add_node",
            ENTRY_ID: entry.entry_id,
            INCLUSION_STRATEGY: InclusionStrategy.SECURITY_S2.value,
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
                STATUS: 1,
                REQUESTED_SECURITY_CLASSES: [0],
            },
        }
    )

    msg = await ws_client.receive_json()
    assert msg["success"]

    assert len(client.async_send_command.call_args_list) == 1
    assert client.async_send_command.call_args[0][0] == {
        "command": "controller.begin_inclusion",
        "options": {
            "strategy": InclusionStrategy.SECURITY_S2,
            "provisioning": QRProvisioningInformation(
                version=QRCodeVersion.S2,
                security_classes=[SecurityClass.S2_UNAUTHENTICATED],
                dsk="test",
                generic_device_class=1,
                specific_device_class=1,
                installer_icon_type=1,
                manufacturer_id=1,
                product_type=1,
                product_id=1,
                application_version="test",
                max_inclusion_request_interval=None,
                uuid=None,
                supported_protocols=None,
                status=ProvisioningEntryStatus.INACTIVE,
                requested_security_classes=[SecurityClass.S2_UNAUTHENTICATED],
            ).to_dict(),
        },
    }

    client.async_send_command.reset_mock()
    client.async_send_command.return_value = {"success": True}

    # Test S2 QR code string
    await ws_client.send_json(
        {
            ID: 5,
            TYPE: "zwave_js/add_node",
            ENTRY_ID: entry.entry_id,
            INCLUSION_STRATEGY: InclusionStrategy.SECURITY_S2.value,
            QR_CODE_STRING: "90testtesttesttesttesttesttesttesttesttesttesttesttest",
        }
    )

    msg = await ws_client.receive_json()
    assert msg["success"]

    assert len(client.async_send_command.call_args_list) == 1
    assert client.async_send_command.call_args[0][0] == {
        "command": "controller.begin_inclusion",
        "options": {
            "strategy": InclusionStrategy.SECURITY_S2,
            "provisioning": "90testtesttesttesttesttesttesttesttesttesttesttesttest",
        },
    }

    client.async_send_command.reset_mock()
    client.async_send_command.return_value = {"success": True}

    # Test S2 DSK string string
    await ws_client.send_json(
        {
            ID: 6,
            TYPE: "zwave_js/add_node",
            ENTRY_ID: entry.entry_id,
            INCLUSION_STRATEGY: InclusionStrategy.SECURITY_S2.value,
            DSK: "test_dsk",
        }
    )

    msg = await ws_client.receive_json()
    assert msg["success"]

    assert len(client.async_send_command.call_args_list) == 1
    assert client.async_send_command.call_args[0][0] == {
        "command": "controller.begin_inclusion",
        "options": {
            "strategy": InclusionStrategy.SECURITY_S2,
            "dsk": "test_dsk",
        },
    }

    client.async_send_command.reset_mock()
    client.async_send_command.return_value = {"success": True}

    # Test Smart Start QR provisioning information with S2 inclusion strategy fails
    await ws_client.send_json(
        {
            ID: 7,
            TYPE: "zwave_js/add_node",
            ENTRY_ID: entry.entry_id,
            INCLUSION_STRATEGY: InclusionStrategy.SECURITY_S2.value,
            QR_PROVISIONING_INFORMATION: {
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
            },
        }
    )

    msg = await ws_client.receive_json()
    assert not msg["success"]

    assert len(client.async_send_command.call_args_list) == 0

    client.async_send_command.reset_mock()
    client.async_send_command.return_value = {"success": True}

    # Test QR provisioning information with S0 inclusion strategy fails
    await ws_client.send_json(
        {
            ID: 8,
            TYPE: "zwave_js/add_node",
            ENTRY_ID: entry.entry_id,
            INCLUSION_STRATEGY: InclusionStrategy.SECURITY_S0,
            QR_PROVISIONING_INFORMATION: {
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
            },
        }
    )

    msg = await ws_client.receive_json()
    assert not msg["success"]

    assert len(client.async_send_command.call_args_list) == 0

    client.async_send_command.reset_mock()
    client.async_send_command.return_value = {" success": True}

    # Test ValueError is caught as failure
    await ws_client.send_json(
        {
            ID: 9,
            TYPE: "zwave_js/add_node",
            ENTRY_ID: entry.entry_id,
            INCLUSION_STRATEGY: InclusionStrategy.DEFAULT.value,
            QR_CODE_STRING: "90testtesttesttesttesttesttesttesttesttesttesttesttest",
        }
    )

    msg = await ws_client.receive_json()
    assert not msg["success"]

    assert len(client.async_send_command.call_args_list) == 0

    # Test FailedZWaveCommand is caught
    with patch(
        f"{CONTROLLER_PATCH_PREFIX}.async_begin_inclusion",
        side_effect=FailedZWaveCommand("failed_command", 1, "error message"),
    ):
        await ws_client.send_json(
            {
                ID: 10,
                TYPE: "zwave_js/add_node",
                ENTRY_ID: entry.entry_id,
            }
        )
        msg = await ws_client.receive_json()

        assert not msg["success"]
        assert msg["error"]["code"] == "zwave_error"
        assert msg["error"]["message"] == "zwave_error: Z-Wave error 1 - error message"

    # Test inclusion already in progress
    client.async_send_command.reset_mock()
    type(client.driver.controller).inclusion_state = PropertyMock(
        return_value=InclusionState.INCLUDING
    )

    # Create a node that's not ready
    node_data = deepcopy(nortek_thermostat.data)  # Copy to allow modification in tests.
    node_data["ready"] = False
    node_data["values"] = {}
    node_data["endpoints"] = {}
    node = Node(client, node_data)
    client.driver.controller.nodes[node.node_id] = node

    await ws_client.send_json(
        {
            ID: 11,
            TYPE: "zwave_js/add_node",
            ENTRY_ID: entry.entry_id,
            INCLUSION_STRATEGY: InclusionStrategy.DEFAULT.value,
        }
    )

    msg = await ws_client.receive_json()
    assert msg["success"]

    # Verify no command was sent since inclusion is already in progress
    assert len(client.async_send_command.call_args_list) == 0

    # Verify we got a node added event
    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "node added"
    assert msg["event"]["node"]["node_id"] == node.node_id

    # Test sending command with not loaded entry fails
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    await ws_client.send_json(
        {ID: 12, TYPE: "zwave_js/add_node", ENTRY_ID: entry.entry_id}
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED