async def test_track_state_change(hass: HomeAssistant) -> None:
    """Test track_state_change."""
    # 2 lists to track how often our callbacks get called
    specific_runs = []
    wildcard_runs = []
    wildercard_runs = []

    def specific_run_callback(entity_id, old_state, new_state):
        specific_runs.append(1)

    # This is the rare use case
    async_track_state_change(hass, "light.Bowl", specific_run_callback, "on", "off")

    @ha.callback
    def wildcard_run_callback(entity_id, old_state, new_state):
        wildcard_runs.append((old_state, new_state))

    # This is the most common use case
    async_track_state_change(hass, "light.Bowl", wildcard_run_callback)

    async def wildercard_run_callback(entity_id, old_state, new_state):
        wildercard_runs.append((old_state, new_state))

    async_track_state_change(hass, MATCH_ALL, wildercard_run_callback)

    # Adding state to state machine
    hass.states.async_set("light.Bowl", "on")
    await hass.async_block_till_done()
    assert len(specific_runs) == 0
    assert len(wildcard_runs) == 1
    assert len(wildercard_runs) == 1
    assert wildcard_runs[-1][0] is None
    assert wildcard_runs[-1][1] is not None

    # Set same state should not trigger a state change/listener
    hass.states.async_set("light.Bowl", "on")
    await hass.async_block_till_done()
    assert len(specific_runs) == 0
    assert len(wildcard_runs) == 1
    assert len(wildercard_runs) == 1

    # State change off -> on
    hass.states.async_set("light.Bowl", "off")
    await hass.async_block_till_done()
    assert len(specific_runs) == 1
    assert len(wildcard_runs) == 2
    assert len(wildercard_runs) == 2

    # State change off -> off
    hass.states.async_set("light.Bowl", "off", {"some_attr": 1})
    await hass.async_block_till_done()
    assert len(specific_runs) == 1
    assert len(wildcard_runs) == 3
    assert len(wildercard_runs) == 3

    # State change off -> on
    hass.states.async_set("light.Bowl", "on")
    await hass.async_block_till_done()
    assert len(specific_runs) == 1
    assert len(wildcard_runs) == 4
    assert len(wildercard_runs) == 4

    hass.states.async_remove("light.bowl")
    await hass.async_block_till_done()
    assert len(specific_runs) == 1
    assert len(wildcard_runs) == 5
    assert len(wildercard_runs) == 5
    assert wildcard_runs[-1][0] is not None
    assert wildcard_runs[-1][1] is None
    assert wildercard_runs[-1][0] is not None
    assert wildercard_runs[-1][1] is None

    # Set state for different entity id
    hass.states.async_set("switch.kitchen", "on")
    await hass.async_block_till_done()
    assert len(specific_runs) == 1
    assert len(wildcard_runs) == 5
    assert len(wildercard_runs) == 6