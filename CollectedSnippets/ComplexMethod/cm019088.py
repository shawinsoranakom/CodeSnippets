async def test_update_unit(hass: HomeAssistant) -> None:
    """Test behavior of changing the unit_time option."""
    # Setup the config entry
    source_id = "sensor.source"
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "name": "My derivative",
            "round": 1.0,
            "source": source_id,
            "unit_time": "min",
            "time_window": {"seconds": 0.0},
        },
        title="My derivative",
    )
    derivative_id = "sensor.my_derivative"
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(derivative_id)
    assert state.state == STATE_UNAVAILABLE
    assert state.attributes.get("unit_of_measurement") is None

    time = dt_util.utcnow()
    with freeze_time(time) as freezer:
        # First state update of the source.
        hass.states.async_set(source_id, 5, {"unit_of_measurement": "dogs"})
        await hass.async_block_till_done()
        state = hass.states.get(derivative_id)
        assert state.state == "0.0"
        assert state.attributes.get("unit_of_measurement") == "dogs/min"

        # Second state update of the source.
        time += timedelta(minutes=1)
        freezer.move_to(time)
        hass.states.async_set(source_id, "7", {"unit_of_measurement": "dogs"})
        await hass.async_block_till_done()
        state = hass.states.get(derivative_id)
        assert state.state == "2.0"
        assert state.attributes.get("unit_of_measurement") == "dogs/min"

        # Update the unit_time from minutes to seconds.
        result = await hass.config_entries.options.async_init(config_entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                "source": source_id,
                "round": 1.0,
                "unit_time": "s",
                "time_window": {"seconds": 0.0},
            },
        )
        await hass.async_block_till_done()

        # Check the state after reconfigure.
        state = hass.states.get(derivative_id)
        assert state.state == "0.0"
        assert state.attributes.get("unit_of_measurement") == "dogs/s"

        # Third state update of the source.
        time += timedelta(seconds=1)
        freezer.move_to(time)
        hass.states.async_set(source_id, "10", {"unit_of_measurement": "dogs"})
        await hass.async_block_till_done()
        state = hass.states.get(derivative_id)
        assert state.state == "3.0"
        assert state.attributes.get("unit_of_measurement") == "dogs/s"

        # Fourth state update of the source.
        time += timedelta(seconds=1)
        freezer.move_to(time)
        hass.states.async_set(source_id, "20", {"unit_of_measurement": "dogs"})
        await hass.async_block_till_done()
        state = hass.states.get(derivative_id)
        assert state.state == "10.0"
        assert state.attributes.get("unit_of_measurement") == "dogs/s"