async def test_valve_switch_with_duration_characteristics(
    hass: HomeAssistant, hk_driver, events: list[Event]
) -> None:
    """Test valve switch with set duration and remaining duration characteristics."""
    entity_id = "switch.sprinkler"

    # Test with duration and end time entities linked
    hass.states.async_set(entity_id, STATE_OFF)
    hass.states.async_set("input_number.valve_duration", "300")
    hass.states.async_set("sensor.valve_end_time", dt_util.utcnow().isoformat())
    await hass.async_block_till_done()

    # Mock switch services to prevent errors
    async_mock_service(hass, SWITCH_DOMAIN, SERVICE_TURN_ON)
    async_mock_service(hass, SWITCH_DOMAIN, SERVICE_TURN_OFF)
    # Mock input_number service for set_duration calls
    call_set_value = async_mock_service(
        hass, INPUT_NUMBER_DOMAIN, INPUT_NUMBER_SERVICE_SET_VALUE
    )

    acc = ValveSwitch(
        hass,
        hk_driver,
        "Sprinkler",
        entity_id,
        5,
        {
            "type": "sprinkler",
            "linked_valve_duration": "input_number.valve_duration",
            "linked_valve_end_time": "sensor.valve_end_time",
        },
    )
    acc.run()
    await hass.async_block_till_done()

    # Test update_duration_chars with both characteristics
    with freeze_time(dt_util.utcnow()):
        hass.states.async_set(
            "sensor.valve_end_time",
            (dt_util.utcnow() + timedelta(seconds=60)).isoformat(),
        )
        hass.states.async_set(entity_id, STATE_OFF)
        await hass.async_block_till_done()
        assert acc.char_set_duration.value == 300
        assert acc.get_remaining_duration() == 60

    # Test get_duration fallback with invalid state
    hass.states.async_set("input_number.valve_duration", "invalid")
    await hass.async_block_till_done()
    assert acc.get_duration() == 0

    # Test get_remaining_duration fallback with invalid state
    hass.states.async_set("sensor.valve_end_time", "invalid")
    await hass.async_block_till_done()
    assert acc.get_remaining_duration() == 0

    # Test get_remaining_duration with end time in the past
    hass.states.async_set(
        "sensor.valve_end_time",
        (dt_util.utcnow() - timedelta(seconds=10)).isoformat(),
    )
    await hass.async_block_till_done()
    assert acc.get_remaining_duration() == 0

    # Test set_duration with negative value
    acc.set_duration(-10)
    await hass.async_block_till_done()
    assert acc.get_duration() == 0
    # Verify the service was called with correct parameters
    assert len(call_set_value) == 1
    assert call_set_value[0].data == {
        "entity_id": "input_number.valve_duration",
        "value": -10,
    }

    # Test set_duration with negative state
    hass.states.async_set("sensor.valve_duration", -10)
    await hass.async_block_till_done()
    assert acc.get_duration() == 0