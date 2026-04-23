async def test_switch_set_state(
    hass: HomeAssistant, hk_driver, events: list[Event]
) -> None:
    """Test if accessory and HA are updated accordingly."""
    code = "1234"
    config = {ATTR_CODE: code}
    entity_id = "alarm_control_panel.test"

    hass.states.async_set(entity_id, None)
    await hass.async_block_till_done()
    acc = SecuritySystem(hass, hk_driver, "SecuritySystem", entity_id, 2, config)
    acc.run()
    await hass.async_block_till_done()

    assert acc.aid == 2
    assert acc.category == 11  # AlarmSystem

    assert acc.char_current_state.value == 3
    assert acc.char_target_state.value == 3

    hass.states.async_set(entity_id, AlarmControlPanelState.ARMED_AWAY)
    await hass.async_block_till_done()
    assert acc.char_target_state.value == 1
    assert acc.char_current_state.value == 1

    hass.states.async_set(entity_id, AlarmControlPanelState.ARMED_HOME)
    await hass.async_block_till_done()
    assert acc.char_target_state.value == 0
    assert acc.char_current_state.value == 0

    hass.states.async_set(entity_id, AlarmControlPanelState.ARMED_NIGHT)
    await hass.async_block_till_done()
    assert acc.char_target_state.value == 2
    assert acc.char_current_state.value == 2

    hass.states.async_set(entity_id, AlarmControlPanelState.DISARMED)
    await hass.async_block_till_done()
    assert acc.char_target_state.value == 3
    assert acc.char_current_state.value == 3

    hass.states.async_set(entity_id, AlarmControlPanelState.TRIGGERED)
    await hass.async_block_till_done()
    assert acc.char_target_state.value == 3
    assert acc.char_current_state.value == 4

    hass.states.async_set(entity_id, STATE_UNKNOWN)
    await hass.async_block_till_done()
    assert acc.char_target_state.value == 3
    assert acc.char_current_state.value == 4

    # Set from HomeKit
    call_arm_home = async_mock_service(
        hass, ALARM_CONTROL_PANEL_DOMAIN, "alarm_arm_home"
    )
    call_arm_away = async_mock_service(
        hass, ALARM_CONTROL_PANEL_DOMAIN, "alarm_arm_away"
    )
    call_arm_night = async_mock_service(
        hass, ALARM_CONTROL_PANEL_DOMAIN, "alarm_arm_night"
    )
    call_disarm = async_mock_service(hass, ALARM_CONTROL_PANEL_DOMAIN, "alarm_disarm")

    acc.char_target_state.client_update_value(0)
    await hass.async_block_till_done()
    assert call_arm_home
    assert call_arm_home[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_arm_home[0].data[ATTR_CODE] == code
    assert acc.char_target_state.value == 0
    assert len(events) == 1
    assert events[-1].data[ATTR_VALUE] is None

    acc.char_target_state.client_update_value(1)
    await hass.async_block_till_done()
    assert call_arm_away
    assert call_arm_away[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_arm_away[0].data[ATTR_CODE] == code
    assert acc.char_target_state.value == 1
    assert len(events) == 2
    assert events[-1].data[ATTR_VALUE] is None

    acc.char_target_state.client_update_value(2)
    await hass.async_block_till_done()
    assert call_arm_night
    assert call_arm_night[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_arm_night[0].data[ATTR_CODE] == code
    assert acc.char_target_state.value == 2
    assert len(events) == 3
    assert events[-1].data[ATTR_VALUE] is None

    acc.char_target_state.client_update_value(3)
    await hass.async_block_till_done()
    assert call_disarm
    assert call_disarm[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_disarm[0].data[ATTR_CODE] == code
    assert acc.char_target_state.value == 3
    assert len(events) == 4
    assert events[-1].data[ATTR_VALUE] is None