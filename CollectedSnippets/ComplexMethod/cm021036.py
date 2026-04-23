async def test_unique_id_migration_when_entity_moves_between_devices(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    mock_client: APIClient,
    mock_esphome_device: MockESPHomeDeviceType,
) -> None:
    """Test that unique_id is migrated when entity moves between devices while entity_id stays the same."""
    # Initial setup: entity on main device
    device_info = {
        "name": "test",
        "devices": [],  # No sub-devices initially
    }

    # Entity on main device
    entity_info = [
        BinarySensorInfo(
            object_id="temperature",
            key=1,
            name="Temperature",  # This field is not used by the integration
            device_id=0,  # Main device
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
    state = hass.states.get("binary_sensor.test_temperature")
    assert state is not None

    # Get the entity from registry
    entity_entry = entity_registry.async_get("binary_sensor.test_temperature")
    assert entity_entry is not None
    initial_unique_id = entity_entry.unique_id
    # Initial unique_id should not have @device_id suffix since it's on main device
    assert "@" not in initial_unique_id

    # Add sub-device to device info
    sub_devices = [
        SubDeviceInfo(device_id=22222222, name="kitchen_controller", area_id=0),
    ]

    # Get the config entry from hass
    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    entry = entries[0]

    # Build device_id_to_name mapping like manager.py does
    entry_data = entry.runtime_data
    entry_data.device_id_to_name = {
        sub_device.device_id: sub_device.name for sub_device in sub_devices
    }

    # Create a new DeviceInfo with sub-devices since it's frozen
    # Get the current device info and convert to dict
    current_device_info = mock_client.device_info.return_value
    device_info_dict = asdict(current_device_info)

    # Update the devices list
    device_info_dict["devices"] = sub_devices

    # Create new DeviceInfo with updated devices
    new_device_info = DeviceInfo(**device_info_dict)

    # Update mock_client to return new device info
    mock_client.device_info.return_value = new_device_info

    # Update entity info - same key and object_id but now on sub-device
    new_entity_info = [
        BinarySensorInfo(
            object_id="temperature",  # Same object_id
            key=1,  # Same key - this is what identifies the entity
            name="Temperature",  # This field is not used
            device_id=22222222,  # Now on sub-device
        ),
    ]

    # Update the entity info by changing what the mock returns
    mock_client.list_entities_services = AsyncMock(return_value=(new_entity_info, []))
    mock_client.device_info_and_list_entities = AsyncMock(
        return_value=(device.device_info, new_entity_info, [])
    )

    # Trigger a reconnect to simulate the entity info update
    await device.mock_disconnect(expected_disconnect=False)
    await device.mock_connect()

    # Wait for entity to be updated
    await hass.async_block_till_done()

    # The entity_id doesn't change when moving between devices
    # Only the unique_id gets updated with @device_id suffix
    state = hass.states.get("binary_sensor.test_temperature")
    assert state is not None

    # Get updated entity from registry - entity_id should be the same
    entity_entry = entity_registry.async_get("binary_sensor.test_temperature")
    assert entity_entry is not None

    # Unique ID should have been migrated to include @device_id
    # This is done by our build_device_unique_id wrapper
    expected_unique_id = f"{initial_unique_id}@22222222"
    assert entity_entry.unique_id == expected_unique_id

    # Entity should now be associated with the sub-device
    sub_device = device_registry.async_get_device(
        identifiers={(DOMAIN, f"{device.device_info.mac_address}_22222222")}
    )
    assert sub_device is not None
    assert entity_entry.device_id == sub_device.id