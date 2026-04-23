async def test_binary_sensors_same_key_different_device_id(
    hass: HomeAssistant,
    mock_client: APIClient,
    mock_esphome_device: MockESPHomeDeviceType,
) -> None:
    """Test binary sensors with same key but different device_id."""
    # Create sub-devices
    sub_devices = [
        SubDeviceInfo(device_id=11111111, name="Sub Device 1", area_id=0),
        SubDeviceInfo(device_id=22222222, name="Sub Device 2", area_id=0),
    ]

    device_info = {
        "name": "test",
        "devices": sub_devices,
    }

    # Both sub-devices have a binary sensor with key=1
    entity_info = [
        BinarySensorInfo(
            object_id="sensor",
            key=1,
            name="Motion",
            device_id=11111111,
        ),
        BinarySensorInfo(
            object_id="sensor",
            key=1,
            name="Motion",
            device_id=22222222,
        ),
    ]

    # States for both sensors with same key but different device_id
    states = [
        BinarySensorState(key=1, state=True, missing_state=False, device_id=11111111),
        BinarySensorState(key=1, state=False, missing_state=False, device_id=22222222),
    ]

    mock_device = await mock_esphome_device(
        mock_client=mock_client,
        device_info=device_info,
        entity_info=entity_info,
        states=states,
    )

    # Verify both entities exist and have correct states
    state1 = hass.states.get("binary_sensor.sub_device_1_motion")
    assert state1 is not None
    assert state1.state == STATE_ON

    state2 = hass.states.get("binary_sensor.sub_device_2_motion")
    assert state2 is not None
    assert state2.state == STATE_OFF

    # Update states to verify they update independently
    mock_device.set_state(
        BinarySensorState(key=1, state=False, missing_state=False, device_id=11111111)
    )
    await hass.async_block_till_done()

    state1 = hass.states.get("binary_sensor.sub_device_1_motion")
    assert state1.state == STATE_OFF

    # Sub device 2 should remain unchanged
    state2 = hass.states.get("binary_sensor.sub_device_2_motion")
    assert state2.state == STATE_OFF

    # Update sub device 2
    mock_device.set_state(
        BinarySensorState(key=1, state=True, missing_state=False, device_id=22222222)
    )
    await hass.async_block_till_done()

    state2 = hass.states.get("binary_sensor.sub_device_2_motion")
    assert state2.state == STATE_ON

    # Sub device 1 should remain unchanged
    state1 = hass.states.get("binary_sensor.sub_device_1_motion")
    assert state1.state == STATE_OFF