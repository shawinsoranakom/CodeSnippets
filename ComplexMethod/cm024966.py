async def test_hass_starting(hass: HomeAssistant) -> None:
    """Test that we cache data."""
    hass.set_state(CoreState.starting)

    now = dt_util.utcnow()
    stored_states = [
        StoredState(State("input_boolean.b0", "on"), None, now),
        StoredState(State("input_boolean.b1", "on"), None, now),
        StoredState(State("input_boolean.b2", "on"), None, now),
    ]

    data = async_get(hass)
    await hass.async_block_till_done()
    await data.store.async_save([state.as_dict() for state in stored_states])

    # Emulate a fresh load
    hass.set_state(CoreState.not_running)
    hass.data.pop(DATA_RESTORE_STATE)
    await async_load(hass)
    data = async_get(hass)

    entity = RestoreEntity()
    entity.hass = hass
    entity.entity_id = "input_boolean.b1"

    all_states = hass.states.async_all()
    assert len(all_states) == 0
    hass.states.async_set("input_boolean.b1", "on")

    # Mock that only b1 is present this run
    with patch(
        "homeassistant.helpers.restore_state.Store.async_save"
    ) as mock_write_data:
        state = await entity.async_get_last_state()
        await hass.async_block_till_done()

    assert state is not None
    assert state.entity_id == "input_boolean.b1"
    assert state.state == "on"
    hass.states.async_remove("input_boolean.b1")

    # Assert that no data was written yet, since hass is still starting.
    assert not mock_write_data.called

    # Finish hass startup
    with patch(
        "homeassistant.helpers.restore_state.Store.async_save"
    ) as mock_write_data:
        hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
        await hass.async_block_till_done()

    # Assert that this session states were written
    assert mock_write_data.called