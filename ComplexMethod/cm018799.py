async def test_age_limit_expiry_with_keep_last_sample(hass: HomeAssistant) -> None:
    """Test that values are removed with given max age."""
    now = dt_util.utcnow()
    current_time = datetime(now.year + 1, 8, 2, 12, 23, tzinfo=dt_util.UTC)

    with freeze_time(current_time) as freezer:
        assert await async_setup_component(
            hass,
            "sensor",
            {
                "sensor": [
                    {
                        "platform": "statistics",
                        "name": "test",
                        "entity_id": "sensor.test_monitored",
                        "state_characteristic": "mean",
                        "sampling_size": 20,
                        "max_age": {"minutes": 4},
                        "keep_last_sample": True,
                    },
                ]
            },
        )
        await hass.async_block_till_done()

        for value in VALUES_NUMERIC:
            current_time += timedelta(minutes=1)
            freezer.move_to(current_time)
            async_fire_time_changed(hass, current_time)
            hass.states.async_set(
                "sensor.test_monitored",
                str(value),
                {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
            )
        await hass.async_block_till_done()

        # After adding all values, we should only see 5 values in memory

        state = hass.states.get("sensor.test")
        new_mean = round(sum(VALUES_NUMERIC[-5:]) / len(VALUES_NUMERIC[-5:]), 2)
        assert state is not None
        assert state.state == str(new_mean)
        assert state.attributes.get("buffer_usage_ratio") == round(5 / 20, 2)
        assert state.attributes.get("age_coverage_ratio") == 1.0

        # Values expire over time. Only two are left

        current_time += timedelta(minutes=3)
        freezer.move_to(current_time)
        async_fire_time_changed(hass, current_time)
        await hass.async_block_till_done()

        state = hass.states.get("sensor.test")
        new_mean = round(sum(VALUES_NUMERIC[-2:]) / len(VALUES_NUMERIC[-2:]), 2)
        assert state is not None
        assert state.state == str(new_mean)
        assert state.attributes.get("buffer_usage_ratio") == round(2 / 20, 2)
        assert state.attributes.get("age_coverage_ratio") == 1 / 4

        # Values expire over time. Only one is left

        current_time += timedelta(minutes=1)
        freezer.move_to(current_time)
        async_fire_time_changed(hass, current_time)
        await hass.async_block_till_done()

        state = hass.states.get("sensor.test")
        new_mean = float(VALUES_NUMERIC[-1])
        assert state is not None
        assert state.state == str(new_mean)
        assert state.attributes.get("buffer_usage_ratio") == round(1 / 20, 2)
        assert state.attributes.get("age_coverage_ratio") == 0

        # Values expire over time. All values expired, but preserve expired last value

        current_time += timedelta(minutes=1)
        freezer.move_to(current_time)
        async_fire_time_changed(hass, current_time)
        await hass.async_block_till_done()

        state = hass.states.get("sensor.test")
        assert state is not None
        assert state.state == str(float(VALUES_NUMERIC[-1]))
        assert state.attributes.get("buffer_usage_ratio") == round(1 / 20, 2)
        assert state.attributes.get("age_coverage_ratio") == 0

        # Indefinitely preserve expired last value

        current_time += timedelta(minutes=1)
        freezer.move_to(current_time)
        async_fire_time_changed(hass, current_time)
        await hass.async_block_till_done()

        state = hass.states.get("sensor.test")
        assert state is not None
        assert state.state == str(float(VALUES_NUMERIC[-1]))
        assert state.attributes.get("buffer_usage_ratio") == round(1 / 20, 2)
        assert state.attributes.get("age_coverage_ratio") == 0

        # New sensor value within max_age, preserved expired value should be dropped
        last_update_val = 123.0
        current_time += timedelta(minutes=1)
        freezer.move_to(current_time)
        async_fire_time_changed(hass, current_time)
        hass.states.async_set(
            "sensor.test_monitored",
            str(last_update_val),
            {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
        )
        await hass.async_block_till_done()

        state = hass.states.get("sensor.test")
        assert state is not None
        assert state.state == str(last_update_val)
        assert state.attributes.get("buffer_usage_ratio") == round(1 / 20, 2)
        assert state.attributes.get("age_coverage_ratio") == 0