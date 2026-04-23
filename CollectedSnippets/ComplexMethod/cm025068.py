async def test_async_track_state_change_filtered(hass: HomeAssistant) -> None:
    """Test async_track_state_change_filtered."""
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
    def callback_that_throws(event: Event[EventStateChangedData]) -> None:
        raise ValueError

    track_single = async_track_state_change_filtered(
        hass, TrackStates(False, {"light.bowl"}, None), single_run_callback
    )
    assert track_single.listeners == {
        "all": False,
        "domains": None,
        "entities": {"light.bowl"},
    }

    track_multi = async_track_state_change_filtered(
        hass, TrackStates(False, {"light.bowl"}, {"switch"}), multiple_run_callback
    )
    assert track_multi.listeners == {
        "all": False,
        "domains": {"switch"},
        "entities": {"light.bowl"},
    }

    track_throws = async_track_state_change_filtered(
        hass, TrackStates(False, {"light.bowl"}, {"switch"}), callback_that_throws
    )
    assert track_throws.listeners == {
        "all": False,
        "domains": {"switch"},
        "entities": {"light.bowl"},
    }

    # Adding state to state machine
    hass.states.async_set("light.Bowl", "on")
    await hass.async_block_till_done()
    assert len(single_entity_id_tracker) == 1
    assert single_entity_id_tracker[-1][0] is None
    assert single_entity_id_tracker[-1][1] is not None
    assert len(multiple_entity_id_tracker) == 1
    assert multiple_entity_id_tracker[-1][0] is None
    assert multiple_entity_id_tracker[-1][1] is not None

    # Set same state should not trigger a state change/listener
    hass.states.async_set("light.Bowl", "on")
    await hass.async_block_till_done()
    assert len(single_entity_id_tracker) == 1
    assert len(multiple_entity_id_tracker) == 1

    # State change off -> on
    hass.states.async_set("light.Bowl", "off")
    await hass.async_block_till_done()
    assert len(single_entity_id_tracker) == 2
    assert len(multiple_entity_id_tracker) == 2

    # State change off -> off
    hass.states.async_set("light.Bowl", "off", {"some_attr": 1})
    await hass.async_block_till_done()
    assert len(single_entity_id_tracker) == 3
    assert len(multiple_entity_id_tracker) == 3

    # State change off -> on
    hass.states.async_set("light.Bowl", "on")
    await hass.async_block_till_done()
    assert len(single_entity_id_tracker) == 4
    assert len(multiple_entity_id_tracker) == 4

    hass.states.async_remove("light.bowl")
    await hass.async_block_till_done()
    assert len(single_entity_id_tracker) == 5
    assert single_entity_id_tracker[-1][0] is not None
    assert single_entity_id_tracker[-1][1] is None
    assert len(multiple_entity_id_tracker) == 5
    assert multiple_entity_id_tracker[-1][0] is not None
    assert multiple_entity_id_tracker[-1][1] is None

    # Set state for different entity id
    hass.states.async_set("switch.kitchen", "on")
    await hass.async_block_till_done()
    assert len(single_entity_id_tracker) == 5
    assert len(multiple_entity_id_tracker) == 6

    track_single.async_remove()
    # Ensure unsubing the listener works
    hass.states.async_set("light.Bowl", "off")
    await hass.async_block_till_done()
    assert len(single_entity_id_tracker) == 5
    assert len(multiple_entity_id_tracker) == 7

    assert track_multi.listeners == {
        "all": False,
        "domains": {"switch"},
        "entities": {"light.bowl"},
    }
    track_multi.async_update_listeners(TrackStates(False, {"light.bowl"}, None))
    assert track_multi.listeners == {
        "all": False,
        "domains": None,
        "entities": {"light.bowl"},
    }
    hass.states.async_set("light.Bowl", "on")
    await hass.async_block_till_done()
    assert len(multiple_entity_id_tracker) == 8
    hass.states.async_set("switch.kitchen", "off")
    await hass.async_block_till_done()
    assert len(multiple_entity_id_tracker) == 8

    track_multi.async_update_listeners(TrackStates(True, None, None))
    hass.states.async_set("switch.kitchen", "off")
    await hass.async_block_till_done()
    assert len(multiple_entity_id_tracker) == 8
    hass.states.async_set("switch.any", "off")
    await hass.async_block_till_done()
    assert len(multiple_entity_id_tracker) == 9

    track_multi.async_remove()
    track_throws.async_remove()