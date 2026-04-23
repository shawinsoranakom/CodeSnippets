async def test_track_state_change_event_chain_single_entity(
    hass: HomeAssistant,
) -> None:
    """Test that adding a new state tracker inside a tracker does not fire right away."""
    tracker_called = []
    chained_tracker_called = []

    chained_tracker_unsub = []
    tracker_unsub = []

    @ha.callback
    def chained_single_run_callback(event: Event[EventStateChangedData]) -> None:
        old_state = event.data["old_state"]
        new_state = event.data["new_state"]

        chained_tracker_called.append((old_state, new_state))

    @ha.callback
    def single_run_callback(event: Event[EventStateChangedData]) -> None:
        old_state = event.data["old_state"]
        new_state = event.data["new_state"]

        tracker_called.append((old_state, new_state))

        chained_tracker_unsub.append(
            async_track_state_change_event(
                hass, "light.bowl", chained_single_run_callback
            )
        )

    tracker_unsub.append(
        async_track_state_change_event(hass, "light.bowl", single_run_callback)
    )

    hass.states.async_set("light.bowl", "on")
    await hass.async_block_till_done()

    assert len(tracker_called) == 1
    assert len(chained_tracker_called) == 0
    assert len(tracker_unsub) == 1
    assert len(chained_tracker_unsub) == 1

    hass.states.async_set("light.bowl", "off")
    await hass.async_block_till_done()

    assert len(tracker_called) == 2
    assert len(chained_tracker_called) == 1
    assert len(tracker_unsub) == 1
    assert len(chained_tracker_unsub) == 2