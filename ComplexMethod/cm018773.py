async def test_charge_switch_service_calls_update_state(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_nrgkick_api: AsyncMock,
) -> None:
    """Test the charge switch calls the API and updates state."""
    await setup_integration(hass, mock_config_entry, platforms=[Platform.SWITCH])

    entity_id = "switch.nrgkick_test_charging_enabled"

    assert (state := hass.states.get(entity_id))
    assert state.state == "on"

    # Pause charging
    # Simulate the device reporting the new paused state after the command.
    control_data = mock_nrgkick_api.get_control.return_value.copy()
    control_data[CONTROL_KEY_CHARGE_PAUSE] = 1
    mock_nrgkick_api.get_control.return_value = control_data
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    assert (state := hass.states.get(entity_id))
    assert state.state == "off"

    # Resume charging
    # Simulate the device reporting the resumed state after the command.
    control_data = mock_nrgkick_api.get_control.return_value.copy()
    control_data[CONTROL_KEY_CHARGE_PAUSE] = 0
    mock_nrgkick_api.get_control.return_value = control_data
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    assert (state := hass.states.get(entity_id))
    assert state.state == "on"

    assert mock_nrgkick_api.set_charge_pause.await_args_list == [
        call(True),
        call(False),
    ]