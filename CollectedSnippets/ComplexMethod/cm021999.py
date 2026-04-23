async def test_update_alarm_device(
    hass: HomeAssistant,
    mock_panel: AsyncMock,
    area: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that alarm panel state changes after arming the panel."""
    await setup_integration(hass, mock_config_entry)
    entity_id = "alarm_control_panel.area1"
    assert hass.states.get(entity_id).state == AlarmControlPanelState.DISARMED

    area.is_arming.return_value = True
    area.is_disarmed.return_value = False

    await hass.services.async_call(
        ALARM_CONTROL_PANEL_DOMAIN,
        SERVICE_ALARM_ARM_AWAY,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    await call_observable(hass, area.status_observer)

    assert hass.states.get(entity_id).state == AlarmControlPanelState.ARMING

    area.is_arming.return_value = False
    area.is_all_armed.return_value = True

    await call_observable(hass, area.status_observer)

    assert hass.states.get(entity_id).state == AlarmControlPanelState.ARMED_AWAY

    area.is_triggered.return_value = True

    await call_observable(hass, area.alarm_observer)

    assert hass.states.get(entity_id).state == AlarmControlPanelState.TRIGGERED

    area.is_triggered.return_value = False

    await call_observable(hass, area.alarm_observer)

    await hass.services.async_call(
        ALARM_CONTROL_PANEL_DOMAIN,
        SERVICE_ALARM_DISARM,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    area.is_all_armed.return_value = False
    area.is_disarmed.return_value = True

    await call_observable(hass, area.status_observer)

    assert hass.states.get(entity_id).state == AlarmControlPanelState.DISARMED
    await hass.services.async_call(
        ALARM_CONTROL_PANEL_DOMAIN,
        SERVICE_ALARM_ARM_HOME,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    area.is_disarmed.return_value = False
    area.is_arming.return_value = True

    await call_observable(hass, area.status_observer)

    assert hass.states.get(entity_id).state == AlarmControlPanelState.ARMING

    area.is_arming.return_value = False
    area.is_part_armed.return_value = True

    await call_observable(hass, area.status_observer)

    assert hass.states.get(entity_id).state == AlarmControlPanelState.ARMED_HOME
    await hass.services.async_call(
        ALARM_CONTROL_PANEL_DOMAIN,
        SERVICE_ALARM_DISARM,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    area.is_part_armed.return_value = False
    area.is_disarmed.return_value = True

    await call_observable(hass, area.status_observer)
    assert hass.states.get(entity_id).state == AlarmControlPanelState.DISARMED