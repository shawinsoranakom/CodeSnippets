async def test_exclude_attributes(
    recorder_mock: Recorder, hass: HomeAssistant, calls: list[ServiceCall]
) -> None:
    """Test automation registered attributes to be excluded."""
    now = dt_util.utcnow()
    await hass.async_block_till_done()
    calls = []
    context = Context()

    @callback
    def record_call(service):
        """Add recorded event to set."""
        calls.append(service)

    hass.services.async_register("test", "script", record_call)

    assert await async_setup_component(
        hass,
        "script",
        {
            "script": {
                "test": {
                    "sequence": {
                        "action": "test.script",
                        "data_template": {"hello": "{{ greeting }}"},
                    }
                }
            }
        },
    )

    await hass.services.async_call(
        script.DOMAIN, "test", {"greeting": "world"}, context=context
    )
    await hass.async_block_till_done()
    await async_wait_recording_done(hass)
    assert len(calls) == 1

    states = await hass.async_add_executor_job(
        get_significant_states, hass, now, None, hass.states.async_entity_ids()
    )
    assert len(states) >= 1
    for entity_states in states.values():
        for state in entity_states:
            assert ATTR_LAST_TRIGGERED not in state.attributes
            assert ATTR_MODE not in state.attributes
            assert ATTR_CUR not in state.attributes
            assert ATTR_LAST_ACTION not in state.attributes
            assert ATTR_MAX not in state.attributes
            assert ATTR_FRIENDLY_NAME in state.attributes