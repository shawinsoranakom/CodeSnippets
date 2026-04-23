async def test_entity_assignment_to_sub_device(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_client: APIClient,
    mock_esphome_device: MockESPHomeDeviceType,
) -> None:
    """Test entities are assigned to correct sub devices."""
    device_registry = dr.async_get(hass)

    # Define sub devices
    sub_devices = [
        SubDeviceInfo(device_id=11111111, name="Motion Sensor", area_id=0),
        SubDeviceInfo(device_id=22222222, name="Door Sensor", area_id=0),
    ]

    device_info = {
        "devices": sub_devices,
    }

    # Create entities that belong to different devices
    entity_info = [
        # Entity for main device (device_id=0)
        BinarySensorInfo(
            object_id="main_sensor",
            key=1,
            name="Main Sensor",
            device_id=0,
        ),
        # Entity for sub device 1
        BinarySensorInfo(
            object_id="motion",
            key=2,
            name="Motion",
            device_id=11111111,
        ),
        # Entity for sub device 2
        BinarySensorInfo(
            object_id="door",
            key=3,
            name="Door",
            device_id=22222222,
        ),
    ]

    states = [
        BinarySensorState(key=1, state=True, missing_state=False, device_id=0),
        BinarySensorState(key=2, state=False, missing_state=False, device_id=11111111),
        BinarySensorState(key=3, state=True, missing_state=False, device_id=22222222),
    ]

    device = await mock_esphome_device(
        mock_client=mock_client,
        device_info=device_info,
        entity_info=entity_info,
        states=states,
    )

    # Check main device
    main_device = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, device.device_info.mac_address)}
    )
    assert main_device is not None

    # Check entities are assigned to correct devices
    main_sensor = entity_registry.async_get("binary_sensor.test_main_sensor")
    assert main_sensor is not None
    assert main_sensor.device_id == main_device.id

    # Check sub device 1 entity
    sub_device_1 = device_registry.async_get_device(
        identifiers={(DOMAIN, f"{device.device_info.mac_address}_11111111")}
    )
    assert sub_device_1 is not None

    motion_sensor = entity_registry.async_get("binary_sensor.motion_sensor_motion")
    assert motion_sensor is not None
    assert motion_sensor.device_id == sub_device_1.id

    # Check sub device 2 entity
    sub_device_2 = device_registry.async_get_device(
        identifiers={(DOMAIN, f"{device.device_info.mac_address}_22222222")}
    )
    assert sub_device_2 is not None

    door_sensor = entity_registry.async_get("binary_sensor.door_sensor_door")
    assert door_sensor is not None
    assert door_sensor.device_id == sub_device_2.id

    # Check states
    assert hass.states.get("binary_sensor.test_main_sensor").state == STATE_ON
    assert hass.states.get("binary_sensor.motion_sensor_motion").state == STATE_OFF
    assert hass.states.get("binary_sensor.door_sensor_door").state == STATE_ON

    # Check entity friendly names
    # Main device entity should have: "{device_name} {entity_name}"
    main_sensor_state = hass.states.get("binary_sensor.test_main_sensor")
    assert main_sensor_state.attributes[ATTR_FRIENDLY_NAME] == "Test Main Sensor"

    # Sub device 1 entity should have: "Motion Sensor Motion"
    motion_sensor_state = hass.states.get("binary_sensor.motion_sensor_motion")
    assert motion_sensor_state.attributes[ATTR_FRIENDLY_NAME] == "Motion Sensor Motion"

    # Sub device 2 entity should have: "Door Sensor Door"
    door_sensor_state = hass.states.get("binary_sensor.door_sensor_door")
    assert door_sensor_state.attributes[ATTR_FRIENDLY_NAME] == "Door Sensor Door"