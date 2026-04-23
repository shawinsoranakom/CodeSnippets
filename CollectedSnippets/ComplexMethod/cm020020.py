async def test_updating(
    hass: HomeAssistant,
    mock_niko_home_control_connection: AsyncMock,
    mock_config_entry: MockConfigEntry,
    climate: AsyncMock,
) -> None:
    """Test updating the thermostat."""
    await setup_integration(hass, mock_config_entry)

    climate.state = 0
    await find_update_callback(mock_niko_home_control_connection, 5)(0)
    assert hass.states.get("climate.thermostat").attributes.get("preset_mode") == "day"
    assert hass.states.get("climate.thermostat").state == "auto"

    climate.state = 1
    await find_update_callback(mock_niko_home_control_connection, 5)(1)
    assert (
        hass.states.get("climate.thermostat").attributes.get("preset_mode") == "night"
    )
    assert hass.states.get("climate.thermostat").state == "auto"

    climate.state = 2
    await find_update_callback(mock_niko_home_control_connection, 5)(2)
    assert hass.states.get("climate.thermostat").state == "auto"
    assert hass.states.get("climate.thermostat").attributes["preset_mode"] == "eco"

    climate.state = 3
    await find_update_callback(mock_niko_home_control_connection, 5)(3)
    assert hass.states.get("climate.thermostat").state == "off"

    climate.state = 4
    await find_update_callback(mock_niko_home_control_connection, 5)(4)
    assert hass.states.get("climate.thermostat").state == "cool"

    climate.state = 5
    await find_update_callback(mock_niko_home_control_connection, 5)(5)
    assert hass.states.get("climate.thermostat").state == "auto"
    assert hass.states.get("climate.thermostat").attributes["preset_mode"] == "prog1"

    climate.state = 6
    await find_update_callback(mock_niko_home_control_connection, 5)(6)
    assert hass.states.get("climate.thermostat").state == "auto"
    assert hass.states.get("climate.thermostat").attributes["preset_mode"] == "prog2"

    climate.state = 7
    await find_update_callback(mock_niko_home_control_connection, 5)(7)
    assert hass.states.get("climate.thermostat").state == "auto"
    assert hass.states.get("climate.thermostat").attributes["preset_mode"] == "prog3"