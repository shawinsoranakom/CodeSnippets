async def test_track_state_change_from_to_state_match(hass: HomeAssistant) -> None:
    """Test track_state_change with from and to state matchers."""
    from_and_to_state_runs = []
    only_from_runs = []
    only_to_runs = []
    match_all_runs = []
    no_to_from_specified_runs = []

    def from_and_to_state_callback(entity_id, old_state, new_state):
        from_and_to_state_runs.append(1)

    def only_from_state_callback(entity_id, old_state, new_state):
        only_from_runs.append(1)

    def only_to_state_callback(entity_id, old_state, new_state):
        only_to_runs.append(1)

    def match_all_callback(entity_id, old_state, new_state):
        match_all_runs.append(1)

    def no_to_from_specified_callback(entity_id, old_state, new_state):
        no_to_from_specified_runs.append(1)

    async_track_state_change(
        hass, "light.Bowl", from_and_to_state_callback, "on", "off"
    )
    async_track_state_change(hass, "light.Bowl", only_from_state_callback, "on", None)
    async_track_state_change(
        hass, "light.Bowl", only_to_state_callback, None, ["off", "standby"]
    )
    async_track_state_change(
        hass, "light.Bowl", match_all_callback, MATCH_ALL, MATCH_ALL
    )
    async_track_state_change(hass, "light.Bowl", no_to_from_specified_callback)

    hass.states.async_set("light.Bowl", "on")
    await hass.async_block_till_done()
    assert len(from_and_to_state_runs) == 0
    assert len(only_from_runs) == 0
    assert len(only_to_runs) == 0
    assert len(match_all_runs) == 1
    assert len(no_to_from_specified_runs) == 1

    hass.states.async_set("light.Bowl", "off")
    await hass.async_block_till_done()
    assert len(from_and_to_state_runs) == 1
    assert len(only_from_runs) == 1
    assert len(only_to_runs) == 1
    assert len(match_all_runs) == 2
    assert len(no_to_from_specified_runs) == 2

    hass.states.async_set("light.Bowl", "on")
    await hass.async_block_till_done()
    assert len(from_and_to_state_runs) == 1
    assert len(only_from_runs) == 1
    assert len(only_to_runs) == 1
    assert len(match_all_runs) == 3
    assert len(no_to_from_specified_runs) == 3

    hass.states.async_set("light.Bowl", "on")
    await hass.async_block_till_done()
    assert len(from_and_to_state_runs) == 1
    assert len(only_from_runs) == 1
    assert len(only_to_runs) == 1
    assert len(match_all_runs) == 3
    assert len(no_to_from_specified_runs) == 3

    hass.states.async_set("light.Bowl", "off")
    await hass.async_block_till_done()
    assert len(from_and_to_state_runs) == 2
    assert len(only_from_runs) == 2
    assert len(only_to_runs) == 2
    assert len(match_all_runs) == 4
    assert len(no_to_from_specified_runs) == 4

    hass.states.async_set("light.Bowl", "off")
    await hass.async_block_till_done()
    assert len(from_and_to_state_runs) == 2
    assert len(only_from_runs) == 2
    assert len(only_to_runs) == 2
    assert len(match_all_runs) == 4
    assert len(no_to_from_specified_runs) == 4