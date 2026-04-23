async def test_entity_device_id_rename_in_yaml(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    mock_client: APIClient,
    mock_esphome_device: MockESPHomeDeviceType,
) -> None:
    """Test that entities are re-added as new when user renames device_id in YAML config."""
    # Initial setup: entity on sub-device with device_id 11111111
    sub_devices = [
        SubDeviceInfo(device_id=11111111, name="old_device", area_id=0),
    ]

    device_info = {
        "name": "test",
        "devices": sub_devices,
    }

    # Entity on sub-device
    entity_info = [
        BinarySensorInfo(
            object_id="sensor",
            key=1,
            name="Sensor",
            device_id=11111111,
        ),
    ]

    states = [
        BinarySensorState(key=1, state=True, missing_state=False, device_id=11111111),
    ]

    device = await mock_esphome_device(
        mock_client=mock_client,
        device_info=device_info,
        entity_info=entity_info,
        states=states,
    )

    # Verify initial entity setup
    state = hass.states.get("binary_sensor.old_device_sensor")
    assert state is not None
    assert state.state == STATE_ON

    # Wait for entity to be registered
    await hass.async_block_till_done()

    # Get the entity from registry
    entity_entry = entity_registry.async_get("binary_sensor.old_device_sensor")
    assert entity_entry is not None
    initial_unique_id = entity_entry.unique_id
    # Should have @11111111 suffix
    assert "@11111111" in initial_unique_id

    # Simulate user renaming device_id in YAML config
    # The device_id hash changes from 11111111 to 99999999
    # This is treated as a completely new device
    renamed_sub_devices = [
        SubDeviceInfo(device_id=99999999, name="renamed_device", area_id=0),
    ]

    # Get the config entry from hass
    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    entry = entries[0]

    # Update device_id_to_name mapping
    entry_data = entry.runtime_data
    entry_data.device_id_to_name = {
        sub_device.device_id: sub_device.name for sub_device in renamed_sub_devices
    }

    # Create new DeviceInfo with renamed device
    current_device_info = mock_client.device_info.return_value
    device_info_dict = asdict(current_device_info)
    device_info_dict["devices"] = renamed_sub_devices
    new_device_info = DeviceInfo(**device_info_dict)
    mock_client.device_info.return_value = new_device_info

    # Entity info now has the new device_id
    new_entity_info = [
        BinarySensorInfo(
            object_id="sensor",  # Same object_id
            key=1,  # Same key
            name="Sensor",
            device_id=99999999,  # New device_id after rename
        ),
    ]

    # Update the entity info
    mock_client.list_entities_services = AsyncMock(return_value=(new_entity_info, []))
    mock_client.device_info_and_list_entities = AsyncMock(
        return_value=(new_device_info, new_entity_info, [])
    )

    # Trigger a reconnect to simulate the YAML config change
    await device.mock_disconnect(expected_disconnect=False)
    await device.mock_connect()
    await hass.async_block_till_done()

    # The old entity should be gone (device was deleted)
    state = hass.states.get("binary_sensor.old_device_sensor")
    assert state is None

    # A new entity should exist with a new entity_id based on the new device name
    # This is a completely new entity, not a migrated one
    state = hass.states.get("binary_sensor.renamed_device_sensor")
    assert state is not None
    assert state.state == STATE_ON

    # Get the new entity from registry
    entity_entry = entity_registry.async_get("binary_sensor.renamed_device_sensor")
    assert entity_entry is not None

    # Unique ID should have the new device_id
    base_unique_id = initial_unique_id.replace("@11111111", "")
    expected_unique_id = f"{base_unique_id}@99999999"
    assert entity_entry.unique_id == expected_unique_id

    # Entity should be associated with the new device
    renamed_device = device_registry.async_get_device(
        identifiers={(DOMAIN, f"{device.device_info.mac_address}_99999999")}
    )
    assert renamed_device is not None
    assert entity_entry.device_id == renamed_device.id