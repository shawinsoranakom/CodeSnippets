async def test_restore_state_pending(hass: HomeAssistant, previous_state) -> None:
    """Ensure PENDING state is restored on startup."""
    time = dt_util.utcnow() - timedelta(seconds=15)
    entity_id = "alarm_control_panel.test"
    attributes = {
        "previous_state": previous_state,
        "next_state": AlarmControlPanelState.TRIGGERED,
    }
    mock_restore_cache(
        hass,
        (
            State(
                entity_id,
                AlarmControlPanelState.TRIGGERED,
                attributes,
                last_updated=time,
            ),
        ),
    )

    hass.set_state(CoreState.starting)
    mock_component(hass, "recorder")

    assert await async_setup_component(
        hass,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "arming_time": 0,
                "delay_time": 60,
                "trigger_time": 60,
                "disarm_after_trigger": False,
            }
        },
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.attributes["previous_state"] == previous_state
    assert state.attributes["next_state"] == AlarmControlPanelState.TRIGGERED
    assert state.state == AlarmControlPanelState.PENDING

    future = time + timedelta(seconds=61)
    with freeze_time(future):
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == AlarmControlPanelState.TRIGGERED

    future = time + timedelta(seconds=121)
    with freeze_time(future):
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == previous_state