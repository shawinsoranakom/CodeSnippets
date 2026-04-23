async def test_humidifier_set_mode(
    hass: HomeAssistant,
    mock_serial_bridge: AsyncMock,
    mock_serial_bridge_config_entry: MockConfigEntry,
) -> None:
    """Test humidifier set mode service."""

    await setup_integration(hass, mock_serial_bridge_config_entry)

    assert (state := hass.states.get(ENTITY_ID))
    assert state.state == STATE_ON
    assert state.attributes[ATTR_HUMIDITY] == 50.0
    assert state.attributes[ATTR_MODE] == MODE_NORMAL

    await hass.services.async_call(
        HUMIDIFIER_DOMAIN,
        SERVICE_SET_MODE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_MODE: MODE_AUTO},
        blocking=True,
    )
    mock_serial_bridge.set_humidity_status.assert_called()

    assert (state := hass.states.get(ENTITY_ID))
    assert state.state == STATE_ON
    assert state.attributes[ATTR_MODE] == MODE_AUTO