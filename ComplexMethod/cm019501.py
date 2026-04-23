async def test_exclude_attributes(recorder_mock: Recorder, hass: HomeAssistant) -> None:
    """Test media_player registered attributes to be excluded."""
    now = dt_util.utcnow()
    await async_setup_component(hass, "homeassistant", {})
    await async_setup_component(
        hass, media_player.DOMAIN, {media_player.DOMAIN: {"platform": "demo"}}
    )
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
            assert ATTR_ENTITY_PICTURE not in state.attributes
            assert ATTR_ENTITY_PICTURE_LOCAL not in state.attributes
            assert ATTR_FRIENDLY_NAME in state.attributes
            assert ATTR_INPUT_SOURCE_LIST not in state.attributes
            assert ATTR_MEDIA_POSITION not in state.attributes
            assert ATTR_MEDIA_POSITION_UPDATED_AT not in state.attributes
            assert ATTR_SOUND_MODE_LIST not in state.attributes