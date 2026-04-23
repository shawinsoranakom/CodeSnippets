async def test_next_change_sensors(
    hass: HomeAssistant, fritz: Mock, next_changes: list, expected_states: list
) -> None:
    """Test next change sensors."""
    device = FritzDeviceClimateMock()
    device.nextchange_endperiod = next_changes[0]
    device.nextchange_temperature = next_changes[1]

    await setup_config_entry(
        hass, MOCK_CONFIG[DOMAIN][CONF_DEVICES][0], ENTITY_ID, device, fritz
    )

    base_name = f"{SENSOR_DOMAIN}.{CONF_FAKE_NAME}"

    state = hass.states.get(f"{base_name}_next_scheduled_change_time")
    assert state
    assert state.state == expected_states[0]

    state = hass.states.get(f"{base_name}_next_scheduled_temperature")
    assert state
    assert state.state == expected_states[1]

    state = hass.states.get(f"{base_name}_next_scheduled_preset")
    assert state
    assert state.state == expected_states[2]

    state = hass.states.get(f"{base_name}_current_scheduled_preset")
    assert state
    assert state.state == expected_states[3]