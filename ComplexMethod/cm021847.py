async def test_hmip_alarm_control_panel(
    hass: HomeAssistant, default_mock_hap_factory: HomeFactory
) -> None:
    """Test HomematicipAlarmControlPanel."""
    entity_id = "alarm_control_panel.hmip_alarm_control_panel"
    entity_name = "HmIP Alarm Control Panel"
    device_model = None
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(
        test_groups=["EXTERNAL", "INTERNAL"]
    )

    ha_state, hmip_device = get_and_check_entity_basics(
        hass, mock_hap, entity_id, entity_name, device_model
    )

    assert ha_state.state == "disarmed"
    assert not hmip_device

    home = mock_hap.home

    await hass.services.async_call(
        "alarm_control_panel", "alarm_arm_away", {"entity_id": entity_id}, blocking=True
    )
    assert home.mock_calls[-1][0] == "set_security_zones_activation_async"
    assert home.mock_calls[-1][1] == (True, True)
    await _async_manipulate_security_zones(
        hass, home, internal_active=True, external_active=True
    )
    assert hass.states.get(entity_id).state == AlarmControlPanelState.ARMED_AWAY

    await hass.services.async_call(
        "alarm_control_panel", "alarm_arm_home", {"entity_id": entity_id}, blocking=True
    )
    assert home.mock_calls[-1][0] == "set_security_zones_activation_async"
    assert home.mock_calls[-1][1] == (False, True)
    await _async_manipulate_security_zones(hass, home, external_active=True)
    assert hass.states.get(entity_id).state == AlarmControlPanelState.ARMED_HOME

    await hass.services.async_call(
        "alarm_control_panel", "alarm_disarm", {"entity_id": entity_id}, blocking=True
    )
    assert home.mock_calls[-1][0] == "set_security_zones_activation_async"
    assert home.mock_calls[-1][1] == (False, False)
    await _async_manipulate_security_zones(hass, home)
    assert hass.states.get(entity_id).state == AlarmControlPanelState.DISARMED

    await hass.services.async_call(
        "alarm_control_panel", "alarm_arm_away", {"entity_id": entity_id}, blocking=True
    )
    assert home.mock_calls[-1][0] == "set_security_zones_activation_async"
    assert home.mock_calls[-1][1] == (True, True)
    await _async_manipulate_security_zones(
        hass, home, internal_active=True, external_active=True, alarm_triggered=True
    )
    assert hass.states.get(entity_id).state == AlarmControlPanelState.TRIGGERED

    await hass.services.async_call(
        "alarm_control_panel", "alarm_arm_home", {"entity_id": entity_id}, blocking=True
    )
    assert home.mock_calls[-1][0] == "set_security_zones_activation_async"
    assert home.mock_calls[-1][1] == (False, True)
    await _async_manipulate_security_zones(
        hass, home, external_active=True, alarm_triggered=True
    )
    assert hass.states.get(entity_id).state == AlarmControlPanelState.TRIGGERED