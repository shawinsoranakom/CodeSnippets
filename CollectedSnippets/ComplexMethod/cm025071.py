async def test_async_track_state_removed_domain(hass: HomeAssistant) -> None:
    """Test async_track_state_removed_domain."""
    single_entity_id_tracker = []
    multiple_entity_id_tracker = []

    @ha.callback
    def single_run_callback(event: Event[EventStateChangedData]) -> None:
        old_state = event.data["old_state"]
        new_state = event.data["new_state"]

        single_entity_id_tracker.append((old_state, new_state))

    @ha.callback
    def multiple_run_callback(event: Event[EventStateChangedData]) -> None:
        old_state = event.data["old_state"]
        new_state = event.data["new_state"]

        multiple_entity_id_tracker.append((old_state, new_state))

    @ha.callback
    def callback_that_throws(event):
        raise ValueError

    unsub_single = async_track_state_removed_domain(
        hass, "light", single_run_callback, job_type=ha.HassJobType.Callback
    )
    unsub_multi = async_track_state_removed_domain(
        hass, ["light", "switch"], multiple_run_callback
    )
    unsub_throws = async_track_state_removed_domain(
        hass, ["light", "switch"], callback_that_throws
    )

    # Adding state to state machine
    hass.states.async_set("light.Bowl", "on")
    hass.states.async_remove("light.Bowl")
    await hass.async_block_till_done()
    assert len(single_entity_id_tracker) == 1
    assert single_entity_id_tracker[-1][1] is None
    assert single_entity_id_tracker[-1][0] is not None
    assert len(multiple_entity_id_tracker) == 1
    assert multiple_entity_id_tracker[-1][1] is None
    assert multiple_entity_id_tracker[-1][0] is not None

    # Added and than removed (light)
    hass.states.async_set("light.Bowl", "on")
    hass.states.async_remove("light.Bowl")
    await hass.async_block_till_done()
    assert len(single_entity_id_tracker) == 2
    assert len(multiple_entity_id_tracker) == 2

    # Added and than removed (light)
    hass.states.async_set("light.Bowl", "off")
    hass.states.async_remove("light.Bowl")
    await hass.async_block_till_done()
    assert len(single_entity_id_tracker) == 3
    assert len(multiple_entity_id_tracker) == 3

    # Added and than removed (light)
    hass.states.async_set("light.Bowl", "off", {"some_attr": 1})
    hass.states.async_remove("light.Bowl")
    await hass.async_block_till_done()
    assert len(single_entity_id_tracker) == 4
    assert len(multiple_entity_id_tracker) == 4

    # Added and than removed (switch)
    hass.states.async_set("switch.kitchen", "on")
    hass.states.async_remove("switch.kitchen")
    await hass.async_block_till_done()
    assert len(single_entity_id_tracker) == 4
    assert len(multiple_entity_id_tracker) == 5

    unsub_single()
    # Ensure unsubing the listener works
    hass.states.async_set("light.new", "off")
    hass.states.async_remove("light.new")
    await hass.async_block_till_done()
    assert len(single_entity_id_tracker) == 4
    assert len(multiple_entity_id_tracker) == 6

    unsub_multi()
    unsub_throws()