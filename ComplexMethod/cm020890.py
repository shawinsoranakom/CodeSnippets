async def test_trigger_with_unused_specific_delay(hass: HomeAssistant) -> None:
    """Test trigger method and switch from pending to triggered."""
    assert await async_setup_component(
        hass,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "code": CODE,
                "delay_time": 5,
                "arming_time": 0,
                "armed_home": {"delay_time": 10},
                "disarm_after_trigger": False,
            }
        },
    )
    await hass.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    assert hass.states.get(entity_id).state == AlarmControlPanelState.DISARMED

    await common.async_alarm_arm_away(hass, CODE)

    assert hass.states.get(entity_id).state == AlarmControlPanelState.ARMED_AWAY

    await common.async_alarm_trigger(hass, entity_id=entity_id)

    state = hass.states.get(entity_id)
    assert state.state == AlarmControlPanelState.PENDING
    assert state.attributes["next_state"] == AlarmControlPanelState.TRIGGERED

    future = dt_util.utcnow() + timedelta(seconds=5)
    with patch(
        "homeassistant.components.manual.alarm_control_panel.dt_util.utcnow",
        return_value=future,
    ):
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.attributes["previous_state"] == AlarmControlPanelState.ARMED_AWAY
    assert state.state == AlarmControlPanelState.TRIGGERED