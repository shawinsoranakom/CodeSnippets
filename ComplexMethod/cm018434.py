async def test_exclude_attributes(recorder_mock: Recorder, hass: HomeAssistant) -> None:
    """Test number registered attributes to be excluded."""
    assert await async_setup_component(hass, "homeassistant", {})
    await async_setup_component(
        hass, number.DOMAIN, {number.DOMAIN: {"platform": "demo"}}
    )
    await hass.async_block_till_done()
    now = dt_util.utcnow()
    async_fire_time_changed(hass, now + timedelta(minutes=5))
    await hass.async_block_till_done()
    await async_wait_recording_done(hass)

    states = await hass.async_add_executor_job(
        get_significant_states, hass, now, None, hass.states.async_entity_ids()
    )
    assert len(states) > 1
    for entity_states in states.values():
        for state in entity_states:
            assert ATTR_MIN not in state.attributes
            assert ATTR_MAX not in state.attributes
            assert ATTR_STEP not in state.attributes
            assert ATTR_MODE not in state.attributes
            assert ATTR_FRIENDLY_NAME in state.attributes