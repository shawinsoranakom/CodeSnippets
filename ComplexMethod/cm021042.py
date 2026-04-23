async def test_generic_numeric_sensor(
    hass: HomeAssistant,
    mock_client: APIClient,
    mock_esphome_device: MockESPHomeDeviceType,
) -> None:
    """Test a generic sensor entity."""
    logging.getLogger("homeassistant.components.esphome").setLevel(logging.DEBUG)
    entity_info = [
        SensorInfo(
            object_id="mysensor",
            key=1,
            name="my sensor",
        )
    ]
    states = [SensorState(key=1, state=50)]
    user_service = []
    mock_device = await mock_esphome_device(
        mock_client=mock_client,
        entity_info=entity_info,
        user_service=user_service,
        states=states,
    )
    state = hass.states.get("sensor.test_my_sensor")
    assert state is not None
    assert state.state == "50"

    # Test updating state
    mock_device.set_state(SensorState(key=1, state=60))
    await hass.async_block_till_done()
    state = hass.states.get("sensor.test_my_sensor")
    assert state is not None
    assert state.state == "60"

    # Test sending the same state again
    mock_device.set_state(SensorState(key=1, state=60))
    await hass.async_block_till_done()
    state = hass.states.get("sensor.test_my_sensor")
    assert state is not None
    assert state.state == "60"

    # Test we can still update after the same state
    mock_device.set_state(SensorState(key=1, state=70))
    await hass.async_block_till_done()
    state = hass.states.get("sensor.test_my_sensor")
    assert state is not None
    assert state.state == "70"

    # Test invalid data from the underlying api does not crash us
    mock_device.set_state(SensorState(key=1, state=object()))
    await hass.async_block_till_done()
    state = hass.states.get("sensor.test_my_sensor")
    assert state is not None
    assert state.state == "70"