async def test_node_model_change(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    zp3111: Node,
    client: MagicMock,
    integration: MockConfigEntry,
) -> None:
    """Test when a node's model is changed due to an updated device config file.

    The device and entities should not be removed.
    """
    device_id = f"{client.driver.controller.home_id}-{zp3111.node_id}"
    device_id_ext = (
        f"{device_id}-{zp3111.manufacturer_id}:"
        f"{zp3111.product_type}:{zp3111.product_id}"
    )

    # Verify device and entities have default names/ids
    device = device_registry.async_get_device(identifiers={(DOMAIN, device_id)})
    assert device
    assert device == device_registry.async_get_device(
        identifiers={(DOMAIN, device_id_ext)}
    )
    assert device.manufacturer == "Vision Security"
    assert device.model == "ZP3111-5"
    assert device.name == "4-in-1 Sensor"
    assert not device.name_by_user

    dev_id = device.id

    motion_entity = "binary_sensor.4_in_1_sensor_motion_detection"
    state = hass.states.get(motion_entity)
    assert state
    assert state.name == "4-in-1 Sensor Motion detection"

    # Customize device and entity names/ids
    device_registry.async_update_device(device.id, name_by_user="Custom Device Name")
    device = device_registry.async_get_device(identifiers={(DOMAIN, device_id)})
    assert device
    assert device.id == dev_id
    assert device == device_registry.async_get_device(
        identifiers={(DOMAIN, device_id_ext)}
    )
    assert device.manufacturer == "Vision Security"
    assert device.model == "ZP3111-5"
    assert device.name == "4-in-1 Sensor"
    assert device.name_by_user == "Custom Device Name"

    custom_entity = "binary_sensor.custom_motion_sensor"
    entity_registry.async_update_entity(
        motion_entity, new_entity_id=custom_entity, name="Custom Entity Name"
    )
    await hass.async_block_till_done()
    assert not hass.states.get(motion_entity)
    state = hass.states.get(custom_entity)
    assert state
    assert state.name == "Custom Entity Name"

    # Unload the integration
    assert await hass.config_entries.async_unload(integration.entry_id)
    await hass.async_block_till_done()
    assert integration.state is ConfigEntryState.NOT_LOADED
    assert not hass.data.get(DOMAIN)

    # Simulate changes to the node labels
    zp3111.device_config.data["description"] = "New Device Name"
    zp3111.device_config.data["label"] = "New Device Model"
    zp3111.device_config.data["manufacturer"] = "New Device Manufacturer"

    # Reload integration, it will re-add the nodes
    integration.add_to_hass(hass)
    await hass.config_entries.async_setup(integration.entry_id)
    await hass.async_block_till_done()

    # Device name changes, but the customization is the same
    device = device_registry.async_get(dev_id)
    assert device
    assert device.id == dev_id
    assert device.manufacturer == "New Device Manufacturer"
    assert device.model == "New Device Model"
    assert device.name == "New Device Name"
    assert device.name_by_user == "Custom Device Name"

    assert not hass.states.get(motion_entity)
    state = hass.states.get(custom_entity)
    assert state
    assert state.name == "Custom Entity Name"