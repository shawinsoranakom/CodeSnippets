async def test_calc_errors(
    hass: HomeAssistant, method: str, expected_states: list[str]
) -> None:
    """Test integration sensor units using a power source."""
    config = {
        "sensor": {
            "platform": "integration",
            "name": "integration",
            "source": "sensor.power",
            "method": method,
        }
    }

    assert await async_setup_component(hass, "sensor", config)

    entity_id = config["sensor"]["source"]

    now = dt_util.utcnow()
    hass.states.async_set(entity_id, None, {})
    await hass.async_block_till_done()

    # With the source sensor in a None state, the Reimann sensor should be
    # unknown
    state = hass.states.get("sensor.integration")
    assert state is not None
    assert state.state == STATE_UNKNOWN

    # Moving from an unknown state to a value is a calc error and should
    # not change the value of the Reimann sensor, unless the method used is "right".
    now += timedelta(seconds=3600)
    with freeze_time(now):
        hass.states.async_set(entity_id, 0, {"device_class": None})
        await hass.async_block_till_done()
    await hass.async_block_till_done()

    state = hass.states.get("sensor.integration")
    assert state is not None
    assert state.state == expected_states[0]

    # With the source sensor updated successfully, the Reimann sensor
    # should have a zero (known) value.
    now += timedelta(seconds=3600)
    with freeze_time(now):
        hass.states.async_set(entity_id, 1, {"device_class": None})
        await hass.async_block_till_done()
    await hass.async_block_till_done()

    state = hass.states.get("sensor.integration")
    assert state is not None
    assert state.state == expected_states[1]

    # Set the source sensor back to a non numeric state
    now += timedelta(seconds=3600)
    with freeze_time(now):
        hass.states.async_set(entity_id, "unexpected", {"device_class": None})
        await hass.async_block_till_done()
    await hass.async_block_till_done()

    state = hass.states.get("sensor.integration")
    assert state is not None
    assert state.state == expected_states[2]