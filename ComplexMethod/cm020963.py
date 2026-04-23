async def test_climate_set_temperature_when_off(
    hass: HomeAssistant,
    mock_serial_bridge: AsyncMock,
    mock_serial_bridge_config_entry: MockConfigEntry,
) -> None:
    """Test climate set temperature service when off."""

    await setup_integration(hass, mock_serial_bridge_config_entry)

    assert (state := hass.states.get(ENTITY_ID))
    assert state.state == HVACMode.HEAT
    assert state.attributes[ATTR_TEMPERATURE] == 5.0

    # Switch climate off
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_HVAC_MODE: HVACMode.OFF},
        blocking=True,
    )
    mock_serial_bridge.set_clima_status.assert_called()

    assert (state := hass.states.get(ENTITY_ID))
    assert state.state == HVACMode.OFF

    # Test set temperature
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_TEMPERATURE: 23},
        blocking=True,
    )
    mock_serial_bridge.set_clima_status.assert_called()

    assert (state := hass.states.get(ENTITY_ID))
    assert state.state == HVACMode.OFF