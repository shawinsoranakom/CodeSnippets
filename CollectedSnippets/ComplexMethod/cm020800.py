async def test_switch_state_updates(
    hass: HomeAssistant,
    mock_airobot_client: AsyncMock,
    mock_settings,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that switch state updates when coordinator refreshes."""
    # Initial state - both switches off
    child_lock = hass.states.get("switch.test_thermostat_child_lock")
    assert child_lock is not None
    assert child_lock.state == STATE_OFF

    actuator_disabled = hass.states.get(
        "switch.test_thermostat_actuator_exercise_disabled"
    )
    assert actuator_disabled is not None
    assert actuator_disabled.state == STATE_OFF

    # Update settings to enable both
    mock_settings.setting_flags.childlock_enabled = True
    mock_settings.setting_flags.actuator_exercise_disabled = True
    mock_airobot_client.get_settings.return_value = mock_settings

    # Trigger coordinator update
    await mock_config_entry.runtime_data.async_refresh()
    await hass.async_block_till_done()

    # Verify states updated
    child_lock = hass.states.get("switch.test_thermostat_child_lock")
    assert child_lock is not None
    assert child_lock.state == STATE_ON

    actuator_disabled = hass.states.get(
        "switch.test_thermostat_actuator_exercise_disabled"
    )
    assert actuator_disabled is not None
    assert actuator_disabled.state == STATE_ON