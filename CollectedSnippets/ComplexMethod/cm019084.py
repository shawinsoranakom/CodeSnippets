async def test_source_unit_change(
    hass: HomeAssistant,
) -> None:
    """Test how derivative responds when the source sensor changes unit."""
    source_id = "sensor.source"
    config = {
        "sensor": {
            "platform": "derivative",
            "name": "derivative",
            "source": source_id,
            "unit_time": "s",
        }
    }

    assert await async_setup_component(hass, "sensor", config)
    await hass.async_block_till_done()
    entity_id = "sensor.derivative"

    state = hass.states.get(entity_id)
    assert state.state == STATE_UNAVAILABLE
    assert state.attributes.get("unit_of_measurement") is None

    time = dt_util.utcnow()
    with freeze_time(time) as freezer:
        # First state update of the source.
        # Derivative does not learn the UoM yet.
        hass.states.async_set(source_id, "5", {"unit_of_measurement": "cats"})
        await hass.async_block_till_done()
        state = hass.states.get(entity_id)
        assert state.state == "0.000"
        assert state.attributes.get("unit_of_measurement") == "cats/s"

        # Second state update of the source.
        time += timedelta(seconds=1)
        freezer.move_to(time)
        hass.states.async_set(source_id, "7", {"unit_of_measurement": "cats"})
        await hass.async_block_till_done()
        state = hass.states.get(entity_id)
        assert state.state == "2.000"
        assert state.attributes.get("unit_of_measurement") == "cats/s"

        # Third state update of the source, source unit changes to dogs.
        # Derivative switches to dogs/s, and resets state to zero, as we
        # don't want to generate bogus data from the change.
        time += timedelta(seconds=1)
        freezer.move_to(time)
        hass.states.async_set(source_id, "12", {"unit_of_measurement": "dogs"})
        await hass.async_block_till_done()
        state = hass.states.get(entity_id)
        assert state.state == "0.000"
        assert state.attributes.get("unit_of_measurement") == "dogs/s"

        # Fourth state update of the source, still dogs.
        # Now correctly updating derivative as dogs/s.
        time += timedelta(seconds=1)
        freezer.move_to(time)
        hass.states.async_set(source_id, "20", {"unit_of_measurement": "dogs"})
        await hass.async_block_till_done()
        state = hass.states.get(entity_id)
        assert state.state == "8.000"
        assert state.attributes.get("unit_of_measurement") == "dogs/s"