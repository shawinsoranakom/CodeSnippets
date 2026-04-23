async def test_existing_node_reinterview(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    client: Client,
    multisensor_6_state: NodeDataType,
    multisensor_6: Node,
    integration: MockConfigEntry,
) -> None:
    """Test we handle a node re-interview firing a node ready event."""
    node = multisensor_6
    assert client.driver is not None
    air_temperature_device_id = f"{client.driver.controller.home_id}-{node.node_id}"
    air_temperature_device_id_ext = (
        f"{air_temperature_device_id}-{node.manufacturer_id}:"
        f"{node.product_type}:{node.product_id}"
    )

    state = hass.states.get(AIR_TEMPERATURE_SENSOR)

    assert state  # entity and device added
    assert state.state != STATE_UNAVAILABLE

    device = device_registry.async_get_device(
        identifiers={(DOMAIN, air_temperature_device_id)}
    )
    assert device
    assert device == device_registry.async_get_device(
        identifiers={(DOMAIN, air_temperature_device_id_ext)}
    )
    assert device.sw_version == "1.12"

    node_state = deepcopy(multisensor_6_state)
    node_state["firmwareVersion"] = "1.13"
    event = Event(
        type="ready",
        data={
            "source": "node",
            "event": "ready",
            "nodeId": node.node_id,
            "nodeState": node_state,
        },
    )
    client.driver.receive_event(event)
    await hass.async_block_till_done()

    state = hass.states.get(AIR_TEMPERATURE_SENSOR)

    assert state
    assert state.state != STATE_UNAVAILABLE
    device = device_registry.async_get_device(
        identifiers={(DOMAIN, air_temperature_device_id)}
    )
    assert device
    assert device == device_registry.async_get_device(
        identifiers={(DOMAIN, air_temperature_device_id_ext)}
    )
    assert device.sw_version == "1.13"