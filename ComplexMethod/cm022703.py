async def test_remaining_duration_characteristic_fallback(
    hass: HomeAssistant, hk_driver, events: list[Event]
) -> None:
    """Test remaining duration falls back to default run time only if valve is active."""
    entity_id = "switch.sprinkler"

    hass.states.async_set(entity_id, STATE_OFF)
    hass.states.async_set("input_number.valve_duration", "900")
    hass.states.async_set("sensor.valve_end_time", None)
    await hass.async_block_till_done()

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

    # Case 1: Remaining duration should always be 0 when accessory is not in use
    hass.states.async_set(entity_id, STATE_OFF)
    await hass.async_block_till_done()
    assert acc.char_in_use.value == 0
    assert acc.get_remaining_duration() == 0

    # Case 2: Remaining duration should fall back to default duration when accessory is in use
    hass.states.async_set(entity_id, STATE_ON)
    await hass.async_block_till_done()
    assert acc.char_in_use.value == 1
    assert acc.get_remaining_duration() == 900

    # Case 3: Remaining duration calculated from linked end time if state is available
    with freeze_time(dt_util.utcnow()):
        # End time is in the futue and valve is in use
        hass.states.async_set(
            "sensor.valve_end_time",
            (dt_util.utcnow() + timedelta(seconds=3600)).isoformat(),
        )
        await hass.async_block_till_done()
        assert acc.char_in_use.value == 1
        assert acc.get_remaining_duration() == 3600

        # End time is in the futue and valve is not in use
        hass.states.async_set(entity_id, STATE_OFF)
        await hass.async_block_till_done()
        assert acc.char_in_use.value == 0
        assert acc.get_remaining_duration() == 3600

        # End time is in the past and valve is in use, returning 0
        hass.states.async_set(entity_id, STATE_ON)
        hass.states.async_set(
            "sensor.valve_end_time",
            (dt_util.utcnow() - timedelta(seconds=3600)).isoformat(),
        )
        await hass.async_block_till_done()
        assert acc.char_in_use.value == 1
        assert acc.get_remaining_duration() == 0

        # End time is in the past and valve is not in use, returning 0
        hass.states.async_set(entity_id, STATE_OFF)
        await hass.async_block_till_done()
        assert acc.char_in_use.value == 0
        assert acc.get_remaining_duration() == 0