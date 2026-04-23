async def test_saving_state_with_serializable_data(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture, setup_recorder: None
) -> None:
    """Test saving data that cannot be serialized does not crash."""
    hass.bus.async_fire("bad_event", {"fail": CannotSerializeMe()})
    hass.states.async_set("test.one", "s1", {"fail": CannotSerializeMe()})
    hass.states.async_set("test.two", "s2", {})
    hass.states.async_set("test.two", "s3", {})
    await async_wait_recording_done(hass)

    with session_scope(hass=hass, read_only=True) as session:
        states = list(
            session.query(
                StatesMeta.entity_id, States.state_id, States.old_state_id, States.state
            ).outerjoin(StatesMeta, States.metadata_id == StatesMeta.metadata_id)
        )
        assert len(states) == 2
        states_by_state = {state.state: state for state in states}
        assert states_by_state["s2"].entity_id == "test.two"
        assert states_by_state["s3"].entity_id == "test.two"
        assert states_by_state["s2"].old_state_id is None
        assert states_by_state["s3"].old_state_id == states_by_state["s2"].state_id

    assert "State is not JSON serializable" in caplog.text