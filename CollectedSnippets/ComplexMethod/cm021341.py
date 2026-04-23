async def test_exclude_attributes(recorder_mock: Recorder, hass: HomeAssistant) -> None:
    """Test climate registered attributes to be excluded."""
    now = dt_util.utcnow()
    await async_setup_component(hass, "homeassistant", {})
    await async_setup_component(
        hass, climate.DOMAIN, {climate.DOMAIN: {"platform": "demo"}}
    )
    await hass.async_block_till_done()
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=5))
    await hass.async_block_till_done()
    await async_wait_recording_done(hass)

    states = await hass.async_add_executor_job(
        get_significant_states, hass, now, None, hass.states.async_entity_ids()
    )
    assert len(states) > 1
    for entity_states in states.values():
        for state in entity_states:
            assert ATTR_FAN_MODES not in state.attributes
            assert ATTR_FRIENDLY_NAME in state.attributes
            assert ATTR_HVAC_MODES not in state.attributes
            assert ATTR_SWING_MODES not in state.attributes
            assert ATTR_MAX_HUMIDITY not in state.attributes
            assert ATTR_MAX_TEMP not in state.attributes
            assert ATTR_MIN_HUMIDITY not in state.attributes
            assert ATTR_MIN_TEMP not in state.attributes
            assert ATTR_PRESET_MODES not in state.attributes
            assert ATTR_TARGET_HUMIDITY_STEP not in state.attributes
            assert ATTR_TARGET_TEMP_STEP not in state.attributes