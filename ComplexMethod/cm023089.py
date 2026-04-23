async def test_replace_different_node(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    multisensor_6: Node,
    multisensor_6_state: NodeDataType,
    hank_binary_switch_state: NodeDataType,
    client: MagicMock,
    integration: MockConfigEntry,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test when a node is replaced with a different node."""
    node_id = multisensor_6.node_id
    state = deepcopy(hank_binary_switch_state)
    state["nodeId"] = node_id

    device_id = f"{client.driver.controller.home_id}-{node_id}"
    multisensor_6_device_id_ext = (
        f"{device_id}-{multisensor_6.manufacturer_id}:"
        f"{multisensor_6.product_type}:{multisensor_6.product_id}"
    )
    hank_device_id_ext = (
        f"{device_id}-{state['manufacturerId']}:"
        f"{state['productType']}:"
        f"{state['productId']}"
    )

    device = device_registry.async_get_device(identifiers={(DOMAIN, device_id)})
    assert device
    assert device == device_registry.async_get_device(
        identifiers={(DOMAIN, multisensor_6_device_id_ext)}
    )
    assert device.manufacturer == "AEON Labs"
    assert device.model == "ZW100"
    dev_id = device.id

    assert hass.states.get(AIR_TEMPERATURE_SENSOR)

    # Remove existing node
    event = Event(
        type="node removed",
        data={
            "source": "controller",
            "event": "node removed",
            "reason": 3,
            "node": multisensor_6_state,
        },
    )
    client.driver.receive_event(event)
    await hass.async_block_till_done()

    # Device should still be there after the node was removed
    device = device_registry.async_get_device(
        identifiers={(DOMAIN, multisensor_6_device_id_ext)}
    )
    assert device
    assert len(device.identifiers) == 2

    # When the node is replaced, a non-ready node added event is emitted
    event = Event(
        type="node added",
        data={
            "source": "controller",
            "event": "node added",
            "node": {
                "nodeId": multisensor_6.node_id,
                "index": 0,
                "status": 4,
                "ready": False,
                "isSecure": False,
                "interviewAttempts": 1,
                "endpoints": [
                    {"nodeId": multisensor_6.node_id, "index": 0, "deviceClass": None}
                ],
                "values": [],
                "deviceClass": None,
                "commandClasses": [],
                "interviewStage": "None",
                "statistics": {
                    "commandsTX": 0,
                    "commandsRX": 0,
                    "commandsDroppedRX": 0,
                    "commandsDroppedTX": 0,
                    "timeoutResponse": 0,
                },
                "isControllerNode": False,
            },
            "result": {},
        },
    )

    # Device is still not removed
    client.driver.receive_event(event)
    await hass.async_block_till_done()

    device = device_registry.async_get(dev_id)
    assert device

    event = Event(
        type="ready",
        data={
            "source": "node",
            "event": "ready",
            "nodeId": node_id,
            "nodeState": state,
        },
    )
    client.driver.receive_event(event)
    await hass.async_block_till_done()

    # node ID based device identifier should be moved from the old multisensor device
    # to the new hank device and both the old and new devices should exist.
    new_device = device_registry.async_get_device(identifiers={(DOMAIN, device_id)})
    assert new_device
    hank_device = device_registry.async_get_device(
        identifiers={(DOMAIN, hank_device_id_ext)}
    )
    assert hank_device
    assert hank_device == new_device
    assert hank_device.identifiers == {
        (DOMAIN, device_id),
        (DOMAIN, hank_device_id_ext),
    }
    multisensor_6_device = device_registry.async_get_device(
        identifiers={(DOMAIN, multisensor_6_device_id_ext)}
    )
    assert multisensor_6_device
    assert multisensor_6_device != new_device
    assert multisensor_6_device.identifiers == {(DOMAIN, multisensor_6_device_id_ext)}

    assert new_device.manufacturer == "HANK Electronics Ltd."
    assert new_device.model == "HKZW-SO01"

    # We keep the old entities in case there are customizations that a user wants to
    # keep. They can always delete the device and that will remove the entities as well.
    assert hass.states.get(AIR_TEMPERATURE_SENSOR)
    assert hass.states.get("switch.smart_plug_with_two_usb_ports")

    # Try to add back the first node to see if the device IDs are correct

    # Remove existing node
    event = Event(
        type="node removed",
        data={
            "source": "controller",
            "event": "node removed",
            "reason": 3,
            "node": state,
        },
    )
    client.driver.receive_event(event)
    await hass.async_block_till_done()

    # Device should still be there after the node was removed
    device = device_registry.async_get_device(
        identifiers={(DOMAIN, hank_device_id_ext)}
    )
    assert device
    assert len(device.identifiers) == 2

    # When the node is replaced, a non-ready node added event is emitted
    event = Event(
        type="node added",
        data={
            "source": "controller",
            "event": "node added",
            "node": {
                "nodeId": multisensor_6.node_id,
                "index": 0,
                "status": 4,
                "ready": False,
                "isSecure": False,
                "interviewAttempts": 1,
                "endpoints": [
                    {"nodeId": multisensor_6.node_id, "index": 0, "deviceClass": None}
                ],
                "values": [],
                "deviceClass": None,
                "commandClasses": [],
                "interviewStage": "None",
                "statistics": {
                    "commandsTX": 0,
                    "commandsRX": 0,
                    "commandsDroppedRX": 0,
                    "commandsDroppedTX": 0,
                    "timeoutResponse": 0,
                },
                "isControllerNode": False,
            },
            "result": {},
        },
    )

    client.driver.receive_event(event)
    await hass.async_block_till_done()

    # Mark node as ready
    event = Event(
        type="ready",
        data={
            "source": "node",
            "event": "ready",
            "nodeId": node_id,
            "nodeState": multisensor_6_state,
        },
    )
    client.driver.receive_event(event)
    await hass.async_block_till_done()

    assert await async_setup_component(hass, "config", {})

    # node ID based device identifier should be moved from the new hank device
    # to the old multisensor device and both the old and new devices should exist.
    old_device = device_registry.async_get_device(identifiers={(DOMAIN, device_id)})
    assert old_device
    hank_device = device_registry.async_get_device(
        identifiers={(DOMAIN, hank_device_id_ext)}
    )
    assert hank_device
    assert hank_device != old_device
    assert hank_device.identifiers == {(DOMAIN, hank_device_id_ext)}
    multisensor_6_device = device_registry.async_get_device(
        identifiers={(DOMAIN, multisensor_6_device_id_ext)}
    )
    assert multisensor_6_device
    assert multisensor_6_device == old_device
    assert multisensor_6_device.identifiers == {
        (DOMAIN, device_id),
        (DOMAIN, multisensor_6_device_id_ext),
    }