async def test_state_changes_during_period_descending(
    hass: HomeAssistant,
) -> None:
    """Test state change during period descending."""
    entity_id = "media_player.test"

    def set_state(state):
        """Set the state."""
        hass.states.async_set(entity_id, state, {"any": 1})
        return hass.states.get(entity_id)

    start = dt_util.utcnow().replace(microsecond=0)
    point = start + timedelta(seconds=1)
    point2 = start + timedelta(seconds=1, microseconds=100)
    point3 = start + timedelta(seconds=1, microseconds=200)
    point4 = start + timedelta(seconds=1, microseconds=300)
    end = point + timedelta(seconds=1, microseconds=400)

    with freeze_time(start) as freezer:
        set_state("idle")
        set_state("YouTube")

        freezer.move_to(point)
        states = [set_state("idle")]

        freezer.move_to(point2)
        states.append(set_state("Netflix"))

        freezer.move_to(point3)
        states.append(set_state("Plex"))

        freezer.move_to(point4)
        states.append(set_state("YouTube"))

        freezer.move_to(end)
        set_state("Netflix")
        set_state("Plex")
    await async_wait_recording_done(hass)

    hist = history.state_changes_during_period(
        hass, start, end, entity_id, no_attributes=False, descending=False
    )

    assert_multiple_states_equal_without_context(states, hist[entity_id])

    hist = history.state_changes_during_period(
        hass, start, end, entity_id, no_attributes=False, descending=True
    )
    assert_multiple_states_equal_without_context(
        states, list(reversed(list(hist[entity_id])))
    )

    start_time = point2 + timedelta(microseconds=10)
    hist = history.state_changes_during_period(
        hass,
        start_time,  # Pick a point where we will generate a start time state
        end,
        entity_id,
        no_attributes=False,
        descending=True,
        include_start_time_state=True,
    )
    hist_states = list(hist[entity_id])
    assert hist_states[-1].last_updated == start_time
    assert hist_states[-1].last_changed == start_time
    assert len(hist_states) == 3
    # Make sure they are in descending order
    assert (
        hist_states[0].last_updated
        > hist_states[1].last_updated
        > hist_states[2].last_updated
    )
    assert (
        hist_states[0].last_changed
        > hist_states[1].last_changed
        > hist_states[2].last_changed
    )
    hist = history.state_changes_during_period(
        hass,
        start_time,  # Pick a point where we will generate a start time state
        end,
        entity_id,
        no_attributes=False,
        descending=False,
        include_start_time_state=True,
    )
    hist_states = list(hist[entity_id])
    assert hist_states[0].last_updated == start_time
    assert hist_states[0].last_changed == start_time
    assert len(hist_states) == 3
    # Make sure they are in ascending order
    assert (
        hist_states[0].last_updated
        < hist_states[1].last_updated
        < hist_states[2].last_updated
    )
    assert (
        hist_states[0].last_changed
        < hist_states[1].last_changed
        < hist_states[2].last_changed
    )