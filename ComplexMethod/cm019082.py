async def test_sub_intervals_instantaneous(hass: HomeAssistant) -> None:
    """Test derivative sensor state."""
    # We simulate the following situation:
    # Value changes from 0 to 10 in 5 seconds (derivative = 2)
    # The max_sub_interval is 20 seconds
    # After max_sub_interval elapses, derivative should change to 0
    # Value changes to 0, 35 seconds after changing to 10 (derivative = -10/35 = -0.29)
    # State goes unavailable, derivative stops changing after that.
    # State goes back to 0, derivative returns to 0 after a max_sub_interval

    max_sub_interval = 20

    config, entity_id = await _setup_sensor(
        hass,
        {
            "unit_time": UnitOfTime.SECONDS,
            "round": 2,
            "max_sub_interval": {"seconds": max_sub_interval},
        },
    )

    base = dt_util.utcnow()
    with freeze_time(base) as freezer:
        freezer.move_to(base)
        hass.states.async_set(entity_id, 0, {}, force_update=True)
        await hass.async_block_till_done()

        now = base + timedelta(seconds=5)
        freezer.move_to(now)
        hass.states.async_set(entity_id, 10, {}, force_update=True)
        await hass.async_block_till_done()

        state = hass.states.get("sensor.power")
        derivative = round(float(state.state), config["sensor"]["round"])
        assert derivative == 2

        # No change yet as sub_interval not elapsed
        now += timedelta(seconds=15)
        async_fire_time_changed(hass, now)
        await hass.async_block_till_done()

        state = hass.states.get("sensor.power")
        derivative = round(float(state.state), config["sensor"]["round"])
        assert derivative == 2

        # After 5 more seconds the sub_interval should fire and derivative should be 0
        now += timedelta(seconds=10)
        async_fire_time_changed(hass, now)
        await hass.async_block_till_done()

        state = hass.states.get("sensor.power")
        derivative = round(float(state.state), config["sensor"]["round"])
        assert derivative == 0

        now += timedelta(seconds=10)
        freezer.move_to(now)
        hass.states.async_set(entity_id, 0, {}, force_update=True)
        await hass.async_block_till_done()

        state = hass.states.get("sensor.power")
        derivative = round(float(state.state), config["sensor"]["round"])
        assert derivative == -0.29

        now += timedelta(seconds=10)
        freezer.move_to(now)
        hass.states.async_set(entity_id, STATE_UNAVAILABLE, {}, force_update=True)
        await hass.async_block_till_done()

        state = hass.states.get("sensor.power")
        assert state.state == STATE_UNAVAILABLE

        now += timedelta(seconds=60)
        async_fire_time_changed(hass, now)
        await hass.async_block_till_done()

        state = hass.states.get("sensor.power")
        assert state.state == STATE_UNAVAILABLE

        now += timedelta(seconds=10)
        freezer.move_to(now)
        hass.states.async_set(entity_id, 0, {}, force_update=True)
        await hass.async_block_till_done()

        state = hass.states.get("sensor.power")
        derivative = round(float(state.state), config["sensor"]["round"])
        assert derivative == 0

        now += timedelta(seconds=max_sub_interval + 1)
        async_fire_time_changed(hass, now)
        await hass.async_block_till_done()

        state = hass.states.get("sensor.power")
        derivative = round(float(state.state), config["sensor"]["round"])
        assert derivative == 0