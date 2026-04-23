async def test_unique_id_migration_sub_device_to_main_device(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    mock_client: APIClient,
    mock_esphome_device: MockESPHomeDeviceType,
) -> None:
    """Test that unique_id is migrated when entity moves from sub-device to main device."""
    # Initial setup: entity on sub-device
    sub_devices = [
        SubDeviceInfo(device_id=22222222, name="kitchen_controller", area_id=0),
    ]

    device_info = {
        "name": "test",
        "devices": sub_devices,
    }

    # Entity on sub-device
    entity_info = [
        BinarySensorInfo(
            object_id="temperature",
            key=1,
            name="Temperature",
            device_id=22222222,  # On sub-device
        ),
    ]

    states = [
        BinarySensorState(key=1, state=True, missing_state=False),
    ]

    device = await mock_esphome_device(
        mock_client=mock_client,
        device_info=device_info,
        entity_info=entity_info,
        states=states,
    )

    # Check initial entity
    state = hass.states.get("binary_sensor.kitchen_controller_temperature")
    assert state is not None

    # Get the entity from registry
    entity_entry = entity_registry.async_get(
        "binary_sensor.kitchen_controller_temperature"
    )
    assert entity_entry is not None
    initial_unique_id = entity_entry.unique_id
    # Initial unique_id should have @device_id suffix since it's on sub-device
    assert "@22222222" in initial_unique_id

    # Update entity info - move to main device
    new_entity_info = [
        BinarySensorInfo(
            object_id="temperature",
            key=1,
            name="Temperature",
            device_id=0,  # Now on main device
        ),
    ]

    # Update the entity info
    mock_client.list_entities_services = AsyncMock(return_value=(new_entity_info, []))
    mock_client.device_info_and_list_entities = AsyncMock(
        return_value=(device.device_info, new_entity_info, [])
    )

    # Trigger a reconnect
    await device.mock_disconnect(expected_disconnect=False)
    await device.mock_connect()
    await hass.async_block_till_done()

    # The entity_id should remain the same
    state = hass.states.get("binary_sensor.kitchen_controller_temperature")
    assert state is not None

    # Get updated entity from registry
    entity_entry = entity_registry.async_get(
        "binary_sensor.kitchen_controller_temperature"
    )
    assert entity_entry is not None

    # Unique ID should have been migrated to remove @device_id suffix
    expected_unique_id = initial_unique_id.replace("@22222222", "")
    assert entity_entry.unique_id == expected_unique_id

    # Entity should now be associated with the main device
    main_device = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, device.device_info.mac_address)}
    )
    assert main_device is not None
    assert entity_entry.device_id == main_device.id