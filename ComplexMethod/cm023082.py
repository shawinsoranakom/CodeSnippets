async def test_existing_node_not_ready(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    client: MagicMock,
    zp3111_not_ready: Node,
    integration: MockConfigEntry,
) -> None:
    """Test we handle a non-ready node that exists during integration setup."""
    node = zp3111_not_ready
    device_id = f"{client.driver.controller.home_id}-{node.node_id}"

    device = device_registry.async_get_device(identifiers={(DOMAIN, device_id)})
    assert device
    assert device.name == f"Node {node.node_id}"
    assert not device.manufacturer
    assert not device.model
    assert not device.sw_version

    device = device_registry.async_get_device(identifiers={(DOMAIN, device_id)})
    assert device
    # no extended device identifier yet
    assert len(device.identifiers) == 1

    entities = er.async_entries_for_device(entity_registry, device.id)
    # the only entities are the node status sensor, and ping button
    assert len(entities) == 2