async def test_exclude_attributes(recorder_mock: Recorder, hass: HomeAssistant) -> None:
    """Test select registered attributes to be excluded."""
    now = dt_util.utcnow()
    assert await async_setup_component(hass, "homeassistant", {})
    await async_setup_component(
        hass, select.DOMAIN, {select.DOMAIN: {"platform": "demo"}}
    )
    await hass.async_block_till_done()
    hass.bus.async_fire("demo_button_pressed")
    await hass.async_block_till_done()
    await async_wait_recording_done(hass)

    states = await hass.async_add_executor_job(
        get_significant_states, hass, now, None, hass.states.async_entity_ids()
    )
    assert len(states) >= 1
    for entity_states in states.values():
        for state in entity_states:
            assert state
            assert ATTR_EVENT_TYPES not in state.attributes
            assert ATTR_FRIENDLY_NAME in state.attributes