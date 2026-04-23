async def test_back_to_back_trigger_with_no_disarm_after_trigger(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    """Test no disarm after back to back trigger."""
    assert await async_setup_component(
        hass,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual_mqtt",
                "name": "test",
                "trigger_time": 5,
                "pending_time": 0,
                "disarm_after_trigger": False,
                "command_topic": "alarm/command",
                "state_topic": "alarm/state",
            }
        },
    )
    await hass.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    assert hass.states.get(entity_id).state == AlarmControlPanelState.DISARMED

    await common.async_alarm_arm_away(hass, CODE, entity_id)

    assert hass.states.get(entity_id).state == AlarmControlPanelState.ARMED_AWAY

    await common.async_alarm_trigger(hass, entity_id=entity_id)

    assert hass.states.get(entity_id).state == AlarmControlPanelState.TRIGGERED

    future = dt_util.utcnow() + timedelta(seconds=5)
    with patch(
        ("homeassistant.components.manual_mqtt.alarm_control_panel.dt_util.utcnow"),
        return_value=future,
    ):
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == AlarmControlPanelState.ARMED_AWAY

    await common.async_alarm_trigger(hass, entity_id=entity_id)

    assert hass.states.get(entity_id).state == AlarmControlPanelState.TRIGGERED

    future = dt_util.utcnow() + timedelta(seconds=5)
    with patch(
        ("homeassistant.components.manual_mqtt.alarm_control_panel.dt_util.utcnow"),
        return_value=future,
    ):
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == AlarmControlPanelState.ARMED_AWAY