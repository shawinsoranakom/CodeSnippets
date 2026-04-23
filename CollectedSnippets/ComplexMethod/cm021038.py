async def test_unique_id_migration_between_sub_devices(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    mock_client: APIClient,
    mock_esphome_device: MockESPHomeDeviceType,
) -> None:
    """Test that unique_id is migrated when entity moves between sub-devices."""
    # Initial setup: two sub-devices
    sub_devices = [
        SubDeviceInfo(device_id=22222222, name="kitchen_controller", area_id=0),
        SubDeviceInfo(device_id=33333333, name="bedroom_controller", area_id=0),
    ]

    device_info = {
        "name": "test",
        "devices": sub_devices,
    }

    # Entity on first sub-device
    entity_info = [
        BinarySensorInfo(
            object_id="temperature",
            key=1,
            name="Temperature",
            device_id=22222222,  # On kitchen_controller
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
    # Initial unique_id should have @22222222 suffix
    assert "@22222222" in initial_unique_id

    # Update entity info - move to second sub-device
    new_entity_info = [
        BinarySensorInfo(
            object_id="temperature",
            key=1,
            name="Temperature",
            device_id=33333333,  # Now on bedroom_controller
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

    # Unique ID should have been migrated from @22222222 to @33333333
    expected_unique_id = initial_unique_id.replace("@22222222", "@33333333")
    assert entity_entry.unique_id == expected_unique_id

    # Entity should now be associated with the second sub-device
    bedroom_device = device_registry.async_get_device(
        identifiers={(DOMAIN, f"{device.device_info.mac_address}_33333333")}
    )
    assert bedroom_device is not None
    assert entity_entry.device_id == bedroom_device.id