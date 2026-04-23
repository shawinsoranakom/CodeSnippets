async def test_entity_friendly_names_with_empty_device_names(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    mock_client: APIClient,
    mock_esphome_device: MockESPHomeDeviceType,
) -> None:
    """Test entity friendly names when sub-devices have empty names."""
    # Define sub devices with different name scenarios
    sub_devices = [
        SubDeviceInfo(device_id=11111111, name="", area_id=0),  # Empty name
        SubDeviceInfo(
            device_id=22222222, name="Kitchen Light", area_id=0
        ),  # Valid name
    ]

    device_info = {
        "devices": sub_devices,
        "friendly_name": "Main Device",
    }

    # Entity on sub-device with empty name
    entity_info = [
        BinarySensorInfo(
            object_id="motion",
            key=1,
            name="Motion Detected",
            device_id=11111111,
        ),
        # Entity on sub-device with valid name
        BinarySensorInfo(
            object_id="status",
            key=2,
            name="Status",
            device_id=22222222,
        ),
        # Entity with empty name on sub-device with valid name
        BinarySensorInfo(
            object_id="sensor",
            key=3,
            name="",  # Empty entity name
            device_id=22222222,
        ),
        # Entity on main device
        BinarySensorInfo(
            object_id="main_status",
            key=4,
            name="Main Status",
            device_id=0,
        ),
    ]

    states = [
        BinarySensorState(key=1, state=True, missing_state=False),
        BinarySensorState(key=2, state=False, missing_state=False),
        BinarySensorState(key=3, state=True, missing_state=False),
        BinarySensorState(key=4, state=True, missing_state=False),
    ]

    await mock_esphome_device(
        mock_client=mock_client,
        device_info=device_info,
        entity_info=entity_info,
        states=states,
    )

    # Check entity friendly name on sub-device with empty name
    # Since sub device has empty name, it falls back to main device name "Main device"
    state_1 = hass.states.get("binary_sensor.main_device_motion_detected")
    assert state_1 is not None
    # With has_entity_name, friendly name is "{device_name} {entity_name}"
    # Since sub-device falls back to main device name: "Main Device Motion Detected"
    assert state_1.attributes[ATTR_FRIENDLY_NAME] == "Main Device Motion Detected"

    # Check entity friendly name on sub-device with valid name
    state_2 = hass.states.get("binary_sensor.kitchen_light_status")
    assert state_2 is not None
    # Device has name "Kitchen Light", entity has name "Status"
    assert state_2.attributes[ATTR_FRIENDLY_NAME] == "Kitchen Light Status"

    # Test entity with empty name on sub-device
    state_3 = hass.states.get("binary_sensor.kitchen_light")
    assert state_3 is not None
    # Entity has empty name, so friendly name is just the device name
    assert state_3.attributes[ATTR_FRIENDLY_NAME] == "Kitchen Light"

    # Test entity on main device
    state_4 = hass.states.get("binary_sensor.main_device_main_status")
    assert state_4 is not None
    assert state_4.attributes[ATTR_FRIENDLY_NAME] == "Main Device Main Status"