async def test_disarm_during_trigger_with_invalid_code(hass: HomeAssistant) -> None:
    """Test disarming while code is invalid."""
    assert await async_setup_component(
        hass,
        alarm_control_panel.DOMAIN,
        {
            "alarm_control_panel": {
                "platform": "manual",
                "name": "test",
                "delay_time": 5,
                "code": "12345",
                "disarm_after_trigger": False,
            }
        },
    )
    await hass.async_block_till_done()

    entity_id = "alarm_control_panel.test"

    assert hass.states.get(entity_id).state == AlarmControlPanelState.DISARMED
    assert (
        hass.states.get(entity_id).attributes[alarm_control_panel.ATTR_CODE_FORMAT]
        == alarm_control_panel.CodeFormat.NUMBER
    )

    await common.async_alarm_trigger(hass)

    assert hass.states.get(entity_id).state == AlarmControlPanelState.PENDING

    with pytest.raises(ServiceValidationError, match=r"^Invalid alarm code provided$"):
        await common.async_alarm_disarm(hass, entity_id=entity_id)

    assert hass.states.get(entity_id).state == AlarmControlPanelState.PENDING

    future = dt_util.utcnow() + timedelta(seconds=5)
    with patch(
        "homeassistant.components.manual.alarm_control_panel.dt_util.utcnow",
        return_value=future,
    ):
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.attributes["previous_state"] == AlarmControlPanelState.DISARMED
    assert state.state == AlarmControlPanelState.TRIGGERED