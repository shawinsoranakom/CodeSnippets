async def test_entity_switches_between_devices(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    mock_client: APIClient,
    mock_esphome_device: MockESPHomeDeviceType,
) -> None:
    """Test that entities can switch between devices correctly."""
    # Define sub devices
    sub_devices = [
        SubDeviceInfo(device_id=11111111, name="Sub Device 1", area_id=0),
        SubDeviceInfo(device_id=22222222, name="Sub Device 2", area_id=0),
    ]

    device_info = {
        "devices": sub_devices,
    }

    # Create initial entity assigned to main device (no device_id)
    entity_info = [
        BinarySensorInfo(
            object_id="sensor",
            key=1,
            name="Test Sensor",
            # device_id omitted - entity belongs to main device
        ),
    ]

    states = [
        BinarySensorState(key=1, state=True, missing_state=False, device_id=0),
    ]

    device = await mock_esphome_device(
        mock_client=mock_client,
        device_info=device_info,
        entity_info=entity_info,
        states=states,
    )

    # Verify entity is on main device
    main_device = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, device.device_info.mac_address)}
    )
    assert main_device is not None

    sensor_entity = entity_registry.async_get("binary_sensor.test_test_sensor")
    assert sensor_entity is not None
    assert sensor_entity.device_id == main_device.id

    # Test 1: Main device → Sub device 1
    updated_entity_info = [
        BinarySensorInfo(
            object_id="sensor",
            key=1,
            name="Test Sensor",
            device_id=11111111,  # Now on sub device 1
        ),
    ]

    # Update the entity info by changing what the mock returns
    mock_client.list_entities_services = AsyncMock(
        return_value=(updated_entity_info, [])
    )
    mock_client.device_info_and_list_entities = AsyncMock(
        return_value=(device.device_info, updated_entity_info, [])
    )
    # Trigger a reconnect to simulate the entity info update
    await device.mock_disconnect(expected_disconnect=False)
    await device.mock_connect()

    # Verify entity is now on sub device 1
    sub_device_1 = device_registry.async_get_device(
        identifiers={(DOMAIN, f"{device.device_info.mac_address}_11111111")}
    )
    assert sub_device_1 is not None

    sensor_entity = entity_registry.async_get("binary_sensor.test_test_sensor")
    assert sensor_entity is not None
    assert sensor_entity.device_id == sub_device_1.id

    # Test 2: Sub device 1 → Sub device 2
    updated_entity_info = [
        BinarySensorInfo(
            object_id="sensor",
            key=1,
            name="Test Sensor",
            device_id=22222222,  # Now on sub device 2
        ),
    ]

    mock_client.list_entities_services = AsyncMock(
        return_value=(updated_entity_info, [])
    )
    mock_client.device_info_and_list_entities = AsyncMock(
        return_value=(device.device_info, updated_entity_info, [])
    )
    await device.mock_disconnect(expected_disconnect=False)
    await device.mock_connect()

    # Verify entity is now on sub device 2
    sub_device_2 = device_registry.async_get_device(
        identifiers={(DOMAIN, f"{device.device_info.mac_address}_22222222")}
    )
    assert sub_device_2 is not None

    sensor_entity = entity_registry.async_get("binary_sensor.test_test_sensor")
    assert sensor_entity is not None
    assert sensor_entity.device_id == sub_device_2.id

    # Test 3: Sub device 2 → Main device
    updated_entity_info = [
        BinarySensorInfo(
            object_id="sensor",
            key=1,
            name="Test Sensor",
            # device_id omitted - back to main device
        ),
    ]

    mock_client.list_entities_services = AsyncMock(
        return_value=(updated_entity_info, [])
    )
    mock_client.device_info_and_list_entities = AsyncMock(
        return_value=(device.device_info, updated_entity_info, [])
    )
    await device.mock_disconnect(expected_disconnect=False)
    await device.mock_connect()

    # Verify entity is back on main device
    sensor_entity = entity_registry.async_get("binary_sensor.test_test_sensor")
    assert sensor_entity is not None
    assert sensor_entity.device_id == main_device.id