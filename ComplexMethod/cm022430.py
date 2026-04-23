async def test_exclude_attributes(recorder_mock: Recorder, hass: HomeAssistant) -> None:
    """Test sun attributes to be excluded."""
    now = dt_util.utcnow()
    await async_setup_component(hass, DOMAIN, {})
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
            assert STATE_ATTR_AZIMUTH not in state.attributes
            assert STATE_ATTR_ELEVATION not in state.attributes
            assert STATE_ATTR_NEXT_DAWN not in state.attributes
            assert STATE_ATTR_NEXT_DUSK not in state.attributes
            assert STATE_ATTR_NEXT_MIDNIGHT not in state.attributes
            assert STATE_ATTR_NEXT_NOON not in state.attributes
            assert STATE_ATTR_NEXT_RISING not in state.attributes
            assert STATE_ATTR_NEXT_SETTING not in state.attributes
            assert STATE_ATTR_RISING not in state.attributes
            assert ATTR_FRIENDLY_NAME in state.attributes