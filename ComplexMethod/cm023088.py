async def test_replace_same_node(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    multisensor_6: Node,
    multisensor_6_state: NodeDataType,
    client: MagicMock,
    integration: MockConfigEntry,
) -> None:
    """Test when a node is replaced with itself that the device remains."""
    node_id = multisensor_6.node_id
    multisensor_6_state = deepcopy(multisensor_6_state)

    device_id = f"{client.driver.controller.home_id}-{node_id}"
    multisensor_6_device_id = (
        f"{device_id}-{multisensor_6.manufacturer_id}:"
        f"{multisensor_6.product_type}:{multisensor_6.product_id}"
    )

    device = device_registry.async_get_device(identifiers={(DOMAIN, device_id)})
    assert device
    assert device == device_registry.async_get_device(
        identifiers={(DOMAIN, multisensor_6_device_id)}
    )
    assert device.manufacturer == "AEON Labs"
    assert device.model == "ZW100"
    dev_id = device.id

    assert hass.states.get(AIR_TEMPERATURE_SENSOR)

    # A replace node event has the extra field "reason"
    # to distinguish it from an exclusion
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
    device = device_registry.async_get(dev_id)
    assert device

    # When the node is replaced, a non-ready node added event is emitted
    event = Event(
        type="node added",
        data={
            "source": "controller",
            "event": "node added",
            "node": {
                "nodeId": node_id,
                "index": 0,
                "status": 4,
                "ready": False,
                "isSecure": False,
                "interviewAttempts": 1,
                "endpoints": [{"nodeId": node_id, "index": 0, "deviceClass": None}],
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
            "nodeState": multisensor_6_state,
        },
    )
    client.driver.receive_event(event)
    await hass.async_block_till_done()

    # Device is the same
    device = device_registry.async_get(dev_id)
    assert device
    assert device == device_registry.async_get_device(identifiers={(DOMAIN, device_id)})
    assert device == device_registry.async_get_device(
        identifiers={(DOMAIN, multisensor_6_device_id)}
    )
    assert device.manufacturer == "AEON Labs"
    assert device.model == "ZW100"

    assert hass.states.get(AIR_TEMPERATURE_SENSOR)