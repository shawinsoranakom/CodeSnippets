async def test_existing_node_not_replaced_when_not_ready(
    hass: HomeAssistant,
    area_registry: ar.AreaRegistry,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    client: MagicMock,
    zp3111: Node,
    zp3111_not_ready_state: NodeDataType,
    zp3111_state: NodeDataType,
    integration: MockConfigEntry,
) -> None:
    """Test when a node added event with a non-ready node is received.

    The existing node should not be replaced, and no customization should be lost.
    """
    kitchen_area = area_registry.async_create("Kitchen")

    device_id = f"{client.driver.controller.home_id}-{zp3111.node_id}"
    device_id_ext = (
        f"{device_id}-{zp3111.manufacturer_id}:"
        f"{zp3111.product_type}:{zp3111.product_id}"
    )

    device = device_registry.async_get_device(identifiers={(DOMAIN, device_id)})
    assert device
    assert device.name == "4-in-1 Sensor"
    assert not device.name_by_user
    assert device.manufacturer == "Vision Security"
    assert device.model == "ZP3111-5"
    assert device.sw_version == "5.1"
    assert not device.area_id
    assert device == device_registry.async_get_device(
        identifiers={(DOMAIN, device_id_ext)}
    )

    motion_entity = "binary_sensor.4_in_1_sensor_motion_detection"
    state = hass.states.get(motion_entity)
    assert state
    assert state.name == "4-in-1 Sensor Motion detection"

    device_registry.async_update_device(
        device.id, name_by_user="Custom Device Name", area_id=kitchen_area.id
    )

    custom_device = device_registry.async_get_device(identifiers={(DOMAIN, device_id)})
    assert custom_device
    assert custom_device.name == "4-in-1 Sensor"
    assert custom_device.name_by_user == "Custom Device Name"
    assert custom_device.manufacturer == "Vision Security"
    assert custom_device.model == "ZP3111-5"
    assert device.sw_version == "5.1"
    assert custom_device.area_id == kitchen_area.id
    assert custom_device == device_registry.async_get_device(
        identifiers={(DOMAIN, device_id_ext)}
    )

    custom_entity = "binary_sensor.custom_motion_sensor"
    entity_registry.async_update_entity(
        motion_entity, new_entity_id=custom_entity, name="Custom Entity Name"
    )
    await hass.async_block_till_done()
    state = hass.states.get(custom_entity)
    assert state
    assert state.name == "Custom Entity Name"
    assert not hass.states.get(motion_entity)

    node_state = deepcopy(zp3111_not_ready_state)
    node_state["isSecure"] = False

    event = Event(
        type="node added",
        data={
            "source": "controller",
            "event": "node added",
            "node": node_state,
            "result": {},
        },
    )
    client.driver.receive_event(event)
    await hass.async_block_till_done()

    device = device_registry.async_get_device(identifiers={(DOMAIN, device_id)})
    assert device
    assert device == device_registry.async_get_device(
        identifiers={(DOMAIN, device_id_ext)}
    )
    assert device.id == custom_device.id
    assert device.identifiers == custom_device.identifiers
    assert device.name == f"Node {zp3111.node_id}"
    assert device.name_by_user == "Custom Device Name"
    assert not device.manufacturer
    assert not device.model
    assert not device.sw_version
    assert device.area_id == kitchen_area.id

    state = hass.states.get(custom_entity)
    assert state
    assert state.name == "Custom Entity Name"

    event = Event(
        type="ready",
        data={
            "source": "node",
            "event": "ready",
            "nodeId": zp3111_state["nodeId"],
            "nodeState": deepcopy(zp3111_state),
        },
    )
    client.driver.receive_event(event)
    await hass.async_block_till_done()

    device = device_registry.async_get_device(identifiers={(DOMAIN, device_id)})
    assert device
    assert device == device_registry.async_get_device(
        identifiers={(DOMAIN, device_id_ext)}
    )
    assert device.id == custom_device.id
    assert device.identifiers == custom_device.identifiers
    assert device.name == "4-in-1 Sensor"
    assert device.name_by_user == "Custom Device Name"
    assert device.manufacturer == "Vision Security"
    assert device.model == "ZP3111-5"
    assert device.area_id == kitchen_area.id
    assert device.sw_version == "5.1"

    state = hass.states.get(custom_entity)
    assert state
    assert state.state != STATE_UNAVAILABLE
    assert state.name == "Custom Entity Name"