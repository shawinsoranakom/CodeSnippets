async def test_arm_away_after_disabled_disarmed(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    """Test pending state with and without zero trigger time."""
    assert await async_setup_component(
        hass,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual_mqtt",
                "name": "test",
                "code": CODE,
                "pending_time": 0,
                "delay_time": 1,
                "armed_away": {"pending_time": 1},
                "disarmed": {"trigger_time": 0},
                "disarm_after_trigger": False,
                "command_topic": "alarm/command",
                "state_topic": "alarm/state",
            }
        },
    )
    await hass.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    assert hass.states.get(entity_id).state == AlarmControlPanelState.DISARMED

    await common.async_alarm_arm_away(hass, CODE)

    state = hass.states.get(entity_id)
    assert state.state == AlarmControlPanelState.PENDING
    assert state.attributes["pre_pending_state"] == AlarmControlPanelState.DISARMED
    assert state.attributes["post_pending_state"] == AlarmControlPanelState.ARMED_AWAY

    await common.async_alarm_trigger(hass, entity_id=entity_id)

    state = hass.states.get(entity_id)
    assert state.state == AlarmControlPanelState.PENDING
    assert state.attributes["pre_pending_state"] == AlarmControlPanelState.DISARMED
    assert state.attributes["post_pending_state"] == AlarmControlPanelState.ARMED_AWAY

    future = dt_util.utcnow() + timedelta(seconds=1)
    with freeze_time(future):
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        assert state.state == AlarmControlPanelState.ARMED_AWAY

        await common.async_alarm_trigger(hass, entity_id=entity_id)

        state = hass.states.get(entity_id)
        assert state.state == AlarmControlPanelState.PENDING
        assert (
            state.attributes["pre_pending_state"] == AlarmControlPanelState.ARMED_AWAY
        )
        assert (
            state.attributes["post_pending_state"] == AlarmControlPanelState.TRIGGERED
        )

    future += timedelta(seconds=1)
    with freeze_time(future):
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == AlarmControlPanelState.TRIGGERED