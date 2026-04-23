async def test_exclude_attributes(
    recorder_mock: Recorder, hass: HomeAssistant, calls: list[ServiceCall]
) -> None:
    """Test automation registered attributes to be excluded."""
    now = dt_util.utcnow()
    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {"trigger": "event", "event_type": "test_event"},
                "actions": {"action": "test.automation", "entity_id": "hello.world"},
            }
        },
    )
    await hass.async_block_till_done()
    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    assert len(calls) == 1
    assert calls[0].data.get(ATTR_ENTITY_ID) == ["hello.world"]
    await async_wait_recording_done(hass)

    states = await hass.async_add_executor_job(
        get_significant_states, hass, now, None, hass.states.async_entity_ids()
    )
    assert len(states) == 1
    for entity_states in states.values():
        for state in entity_states:
            assert ATTR_LAST_TRIGGERED not in state.attributes
            assert ATTR_MODE not in state.attributes
            assert ATTR_CUR not in state.attributes
            assert CONF_ID not in state.attributes
            assert ATTR_MAX not in state.attributes
            assert ATTR_FRIENDLY_NAME in state.attributes