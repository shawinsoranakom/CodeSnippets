async def test_trigger_with_pending(hass: HomeAssistant) -> None:
    """Test arm home method."""
    assert await async_setup_component(
        hass,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "delay_time": 2,
                "trigger_time": 3,
                "disarm_after_trigger": False,
            }
        },
    )
    await hass.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    assert hass.states.get(entity_id).state == AlarmControlPanelState.DISARMED

    await common.async_alarm_trigger(hass)

    assert hass.states.get(entity_id).state == AlarmControlPanelState.PENDING

    state = hass.states.get(entity_id)
    assert state.attributes["next_state"] == AlarmControlPanelState.TRIGGERED

    future = dt_util.utcnow() + timedelta(seconds=2)
    with patch(
        "homeassistant.components.manual.alarm_control_panel.dt_util.utcnow",
        return_value=future,
    ):
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.attributes["previous_state"] == AlarmControlPanelState.DISARMED
    assert state.state == AlarmControlPanelState.TRIGGERED

    future = dt_util.utcnow() + timedelta(seconds=5)
    with patch(
        "homeassistant.components.manual.alarm_control_panel.dt_util.utcnow",
        return_value=future,
    ):
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == AlarmControlPanelState.DISARMED