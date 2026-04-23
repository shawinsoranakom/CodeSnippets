async def test_exclude_attributes(hass: HomeAssistant) -> None:
    """Test attributes to be excluded."""
    now = dt_util.utcnow()
    assert await async_setup_component(
        hass, DOMAIN, {DOMAIN: {"test": {"min": 0, "max": 100}}}
    )

    state = hass.states.get("input_number.test")
    assert state
    assert state.attributes[ATTR_EDITABLE] is False
    assert state.attributes[ATTR_MIN] == 0
    assert state.attributes[ATTR_MAX] == 100
    assert state.attributes[ATTR_STEP] == 1
    assert state.attributes[ATTR_MODE] == "slider"

    await hass.async_block_till_done()
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=5))
    await hass.async_block_till_done()
    await async_wait_recording_done(hass)

    states = await hass.async_add_executor_job(
        get_significant_states, hass, now, None, hass.states.async_entity_ids()
    )
    assert len(states) >= 1
    for entity_states in states.values():
        for state in entity_states:
            assert ATTR_EDITABLE not in state.attributes
            assert ATTR_MIN not in state.attributes
            assert ATTR_MAX not in state.attributes
            assert ATTR_STEP not in state.attributes
            assert ATTR_MODE not in state.attributes