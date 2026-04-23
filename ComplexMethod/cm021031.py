async def test_deep_sleep_device(
    hass: HomeAssistant,
    mock_client: APIClient,
    hass_storage: dict[str, Any],
    mock_esphome_device: MockESPHomeDeviceType,
) -> None:
    """Test a deep sleep device."""
    entity_info = [
        BinarySensorInfo(
            object_id="mybinary_sensor",
            key=1,
            name="my binary_sensor",
        ),
        SensorInfo(
            object_id="my_sensor",
            key=3,
            name="my sensor",
        ),
    ]
    states = [
        BinarySensorState(key=1, state=True, missing_state=False),
        BinarySensorState(key=2, state=True, missing_state=False),
        SensorState(key=3, state=123.0, missing_state=False),
    ]
    mock_device = await mock_esphome_device(
        mock_client=mock_client,
        entity_info=entity_info,
        states=states,
        device_info={"has_deep_sleep": True},
    )
    state = hass.states.get("binary_sensor.test_my_binary_sensor")
    assert state is not None
    assert state.state == STATE_ON
    state = hass.states.get("sensor.test_my_sensor")
    assert state is not None
    assert state.state == "123.0"

    await mock_device.mock_disconnect(False)
    await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.test_my_binary_sensor")
    assert state is not None
    assert state.state == STATE_UNAVAILABLE
    state = hass.states.get("sensor.test_my_sensor")
    assert state is not None
    assert state.state == STATE_UNAVAILABLE

    await mock_device.mock_connect()
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.test_my_binary_sensor")
    assert state is not None
    assert state.state == STATE_ON
    state = hass.states.get("sensor.test_my_sensor")
    assert state is not None
    assert state.state == "123.0"

    await mock_device.mock_disconnect(True)
    await hass.async_block_till_done()
    await mock_device.mock_connect()
    await hass.async_block_till_done()
    mock_device.set_state(BinarySensorState(key=1, state=False, missing_state=False))
    mock_device.set_state(SensorState(key=3, state=56, missing_state=False))
    await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.test_my_binary_sensor")
    assert state is not None
    assert state.state == STATE_OFF
    state = hass.states.get("sensor.test_my_sensor")
    assert state is not None
    assert state.state == "56"

    await mock_device.mock_disconnect(True)
    await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.test_my_binary_sensor")
    assert state is not None
    assert state.state == STATE_OFF
    state = hass.states.get("sensor.test_my_sensor")
    assert state is not None
    assert state.state == "56"

    await mock_device.mock_connect()
    await hass.async_block_till_done()
    await mock_device.mock_disconnect(False)
    await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.test_my_binary_sensor")
    assert state is not None
    assert state.state == STATE_UNAVAILABLE
    state = hass.states.get("sensor.test_my_sensor")
    assert state is not None
    assert state.state == STATE_UNAVAILABLE

    await mock_device.mock_connect()
    await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.test_my_binary_sensor")
    assert state is not None
    assert state.state == STATE_ON
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
    await hass.async_block_till_done()
    # Verify we do not dispatch any more state updates or
    # availability updates after the stop event is fired
    state = hass.states.get("binary_sensor.test_my_binary_sensor")
    assert state is not None
    assert state.state == STATE_ON