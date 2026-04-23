async def test_get_significant_states_only(
    hass: HomeAssistant,
) -> None:
    """Test significant states when significant_states_only is set."""
    entity_id = "sensor.test"

    def set_state(state, **kwargs):
        """Set the state."""
        hass.states.async_set(entity_id, state, **kwargs)
        return hass.states.get(entity_id)

    start = dt_util.utcnow() - timedelta(minutes=4)
    points = [start + timedelta(minutes=i) for i in range(1, 4)]

    states = []
    with freeze_time(start) as freezer:
        set_state("123", attributes={"attribute": 10.64})

        freezer.move_to(points[0])
        # Attributes are different, state not
        states.append(set_state("123", attributes={"attribute": 21.42}))

        freezer.move_to(points[1])
        # state is different, attributes not
        states.append(set_state("32", attributes={"attribute": 21.42}))

        freezer.move_to(points[2])
        # everything is different
        states.append(set_state("412", attributes={"attribute": 54.23}))
    await async_wait_recording_done(hass)

    hist = history.get_significant_states(
        hass,
        start,
        significant_changes_only=True,
        entity_ids=list({state.entity_id for state in states}),
    )

    assert len(hist[entity_id]) == 2
    assert not any(
        state.last_updated == states[0].last_updated for state in hist[entity_id]
    )
    assert any(
        state.last_updated == states[1].last_updated for state in hist[entity_id]
    )
    assert any(
        state.last_updated == states[2].last_updated for state in hist[entity_id]
    )

    hist = history.get_significant_states(
        hass,
        start,
        significant_changes_only=False,
        entity_ids=list({state.entity_id for state in states}),
    )

    assert len(hist[entity_id]) == 3
    assert_multiple_states_equal_without_context_and_last_changed(
        states, hist[entity_id]
    )