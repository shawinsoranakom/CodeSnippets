async def test_climate_preset_mode_when_off(
    hass: HomeAssistant,
    mock_serial_bridge: AsyncMock,
    mock_serial_bridge_config_entry: MockConfigEntry,
) -> None:
    """Test climate preset mode service when off."""

    await setup_integration(hass, mock_serial_bridge_config_entry)

    assert (state := hass.states.get(ENTITY_ID))
    assert state.state == HVACMode.HEAT
    assert state.attributes[ATTR_TEMPERATURE] == 5.0
    assert state.attributes[ATTR_PRESET_MODE] == PRESET_MODE_MANUAL

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )
    mock_serial_bridge.set_clima_status.assert_called()

    assert (state := hass.states.get(ENTITY_ID))
    assert state.state == HVACMode.OFF

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_PRESET_MODE: PRESET_MODE_AUTO},
        blocking=True,
    )
    mock_serial_bridge.set_clima_status.assert_called()

    assert (state := hass.states.get(ENTITY_ID))
    assert state.state == HVACMode.OFF