async def test_arming(hass: HomeAssistant, hk_driver) -> None:
    """Test to make sure arming sets the right state."""
    entity_id = "alarm_control_panel.test"

    hass.states.async_set(entity_id, None)

    acc = SecuritySystem(hass, hk_driver, "SecuritySystem", entity_id, 2, {})
    acc.run()
    await hass.async_block_till_done()

    hass.states.async_set(entity_id, AlarmControlPanelState.ARMED_AWAY)
    await hass.async_block_till_done()
    assert acc.char_target_state.value == 1
    assert acc.char_current_state.value == 1

    hass.states.async_set(entity_id, AlarmControlPanelState.ARMED_HOME)
    await hass.async_block_till_done()
    assert acc.char_target_state.value == 0
    assert acc.char_current_state.value == 0

    hass.states.async_set(entity_id, AlarmControlPanelState.ARMED_VACATION)
    await hass.async_block_till_done()
    assert acc.char_target_state.value == 1
    assert acc.char_current_state.value == 1

    hass.states.async_set(entity_id, AlarmControlPanelState.ARMED_NIGHT)
    await hass.async_block_till_done()
    assert acc.char_target_state.value == 2
    assert acc.char_current_state.value == 2

    hass.states.async_set(entity_id, AlarmControlPanelState.ARMING)
    await hass.async_block_till_done()
    assert acc.char_target_state.value == 1
    assert acc.char_current_state.value == 3

    hass.states.async_set(entity_id, AlarmControlPanelState.DISARMED)
    await hass.async_block_till_done()
    assert acc.char_target_state.value == 3
    assert acc.char_current_state.value == 3

    hass.states.async_set(entity_id, AlarmControlPanelState.ARMED_AWAY)
    await hass.async_block_till_done()
    assert acc.char_target_state.value == 1
    assert acc.char_current_state.value == 1

    hass.states.async_set(entity_id, AlarmControlPanelState.TRIGGERED)
    await hass.async_block_till_done()
    assert acc.char_target_state.value == 1
    assert acc.char_current_state.value == 4