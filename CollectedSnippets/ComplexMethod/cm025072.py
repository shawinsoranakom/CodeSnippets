async def test_track_template(hass: HomeAssistant) -> None:
    """Test tracking template."""
    specific_runs = []
    wildcard_runs = []
    wildercard_runs = []

    template_condition = Template("{{states.switch.test.state == 'on'}}", hass)
    template_condition_var = Template(
        "{{states.switch.test.state == 'on' and test == 5}}", hass
    )

    hass.states.async_set("switch.test", "off")

    def specific_run_callback(entity_id, old_state, new_state):
        specific_runs.append(1)

    async_track_template(hass, template_condition, specific_run_callback)

    @ha.callback
    def wildcard_run_callback(entity_id, old_state, new_state):
        wildcard_runs.append((old_state, new_state))

    async_track_template(hass, template_condition, wildcard_run_callback)

    async def wildercard_run_callback(entity_id, old_state, new_state):
        wildercard_runs.append((old_state, new_state))

    async_track_template(
        hass, template_condition_var, wildercard_run_callback, {"test": 5}
    )

    hass.states.async_set("switch.test", "on")
    await hass.async_block_till_done()

    assert len(specific_runs) == 1
    assert len(wildcard_runs) == 1
    assert len(wildercard_runs) == 1

    hass.states.async_set("switch.test", "on")
    await hass.async_block_till_done()

    assert len(specific_runs) == 1
    assert len(wildcard_runs) == 1
    assert len(wildercard_runs) == 1

    hass.states.async_set("switch.test", "off")
    await hass.async_block_till_done()

    assert len(specific_runs) == 1
    assert len(wildcard_runs) == 1
    assert len(wildercard_runs) == 1

    hass.states.async_set("switch.test", "off")
    await hass.async_block_till_done()

    assert len(specific_runs) == 1
    assert len(wildcard_runs) == 1
    assert len(wildercard_runs) == 1

    hass.states.async_set("switch.test", "on")
    await hass.async_block_till_done()

    assert len(specific_runs) == 2
    assert len(wildcard_runs) == 2
    assert len(wildercard_runs) == 2

    template_iterate = Template("{{ (states.switch | length) > 0 }}", hass)
    iterate_calls = []

    @ha.callback
    def iterate_callback(entity_id, old_state, new_state):
        iterate_calls.append((entity_id, old_state, new_state))

    async_track_template(hass, template_iterate, iterate_callback)
    await hass.async_block_till_done()

    hass.states.async_set("switch.new", "on")
    await hass.async_block_till_done()

    assert len(iterate_calls) == 1
    assert iterate_calls[0][0] == "switch.new"
    assert iterate_calls[0][1] is None
    assert iterate_calls[0][2].state == "on"