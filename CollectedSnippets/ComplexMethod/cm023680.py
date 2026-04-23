async def test_purge_old_states(hass: HomeAssistant, recorder_mock: Recorder) -> None:
    """Test deleting old states."""
    assert recorder_mock.states_manager.oldest_ts is None
    oldest_ts = recorder_mock.states_manager.oldest_ts

    await _add_test_states(hass)

    # make sure we start with 6 states
    with session_scope(hass=hass) as session:
        states = session.query(States)
        state_attributes = session.query(StateAttributes)

        assert states.count() == 6
        assert states[0].old_state_id is None
        assert states[5].old_state_id == states[4].state_id
        assert state_attributes.count() == 3

        events = session.query(Events).filter(Events.event_type == "state_changed")
        assert events.count() == 0

        assert recorder_mock.states_manager.oldest_ts != oldest_ts
        assert recorder_mock.states_manager.oldest_ts == states[0].last_updated_ts
        oldest_ts = recorder_mock.states_manager.oldest_ts

    assert "test.recorder2" in recorder_mock.states_manager._last_committed_id

    purge_before = dt_util.utcnow() - timedelta(days=4)

    # run purge_old_data()
    finished = purge_old_data(
        recorder_mock,
        purge_before,
        states_batch_size=1,
        events_batch_size=1,
        repack=False,
    )
    assert not finished
    # states_manager.oldest_ts is not updated until after the purge is complete
    assert recorder_mock.states_manager.oldest_ts == oldest_ts

    with session_scope(hass=hass) as session:
        states = session.query(States)
        state_attributes = session.query(StateAttributes)
        assert states.count() == 2
        assert state_attributes.count() == 1

    assert "test.recorder2" in recorder_mock.states_manager._last_committed_id

    with session_scope(hass=hass) as session:
        states_after_purge = list(session.query(States))
        # Since these states are deleted in batches, we can't guarantee the order
        # but we can look them up by state
        state_map_by_state = {state.state: state for state in states_after_purge}
        dontpurgeme_5 = state_map_by_state["dontpurgeme_5"]
        dontpurgeme_4 = state_map_by_state["dontpurgeme_4"]

        assert dontpurgeme_5.old_state_id == dontpurgeme_4.state_id
        assert dontpurgeme_4.old_state_id is None

    finished = purge_old_data(recorder_mock, purge_before, repack=False)
    assert finished
    # states_manager.oldest_ts should now be updated
    assert recorder_mock.states_manager.oldest_ts != oldest_ts

    with session_scope(hass=hass) as session:
        states = session.query(States)
        state_attributes = session.query(StateAttributes)
        assert states.count() == 2
        assert state_attributes.count() == 1

        assert recorder_mock.states_manager.oldest_ts != oldest_ts
        assert recorder_mock.states_manager.oldest_ts == states[0].last_updated_ts
        oldest_ts = recorder_mock.states_manager.oldest_ts

    assert "test.recorder2" in recorder_mock.states_manager._last_committed_id

    # run purge_old_data again
    purge_before = dt_util.utcnow()
    finished = purge_old_data(
        recorder_mock,
        purge_before,
        states_batch_size=1,
        events_batch_size=1,
        repack=False,
    )
    assert not finished
    # states_manager.oldest_ts is not updated until after the purge is complete
    assert recorder_mock.states_manager.oldest_ts == oldest_ts

    with session_scope(hass=hass) as session:
        assert states.count() == 0
        assert state_attributes.count() == 0

    assert "test.recorder2" not in recorder_mock.states_manager._last_committed_id

    # Add some more states
    await _add_test_states(hass)

    # make sure we start with 6 states
    with session_scope(hass=hass) as session:
        states = session.query(States)
        assert states.count() == 6
        assert states[0].old_state_id is None
        assert states[5].old_state_id == states[4].state_id

        events = session.query(Events).filter(Events.event_type == "state_changed")
        assert events.count() == 0
        assert "test.recorder2" in recorder_mock.states_manager._last_committed_id

        state_attributes = session.query(StateAttributes)
        assert state_attributes.count() == 3