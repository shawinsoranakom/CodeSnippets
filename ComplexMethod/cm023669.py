async def test_saving_sets_old_state(hass: HomeAssistant, setup_recorder: None) -> None:
    """Test saving sets old state."""
    hass.states.async_set("test.one", "s1", {})
    hass.states.async_set("test.two", "s2", {})
    hass.states.async_set("test.one", "s3", {})
    hass.states.async_set("test.two", "s4", {})
    await async_wait_recording_done(hass)

    with session_scope(hass=hass, read_only=True) as session:
        states = list(
            session.query(
                StatesMeta.entity_id, States.state_id, States.old_state_id, States.state
            ).outerjoin(StatesMeta, States.metadata_id == StatesMeta.metadata_id)
        )
        assert len(states) == 4
        states_by_state = {state.state: state for state in states}

        assert states_by_state["s1"].entity_id == "test.one"
        assert states_by_state["s2"].entity_id == "test.two"
        assert states_by_state["s3"].entity_id == "test.one"
        assert states_by_state["s4"].entity_id == "test.two"

        assert states_by_state["s1"].old_state_id is None
        assert states_by_state["s2"].old_state_id is None
        assert states_by_state["s3"].old_state_id == states_by_state["s1"].state_id
        assert states_by_state["s4"].old_state_id == states_by_state["s2"].state_id