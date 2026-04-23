async def test_humidifier_set_status(
    hass: HomeAssistant,
    mock_serial_bridge: AsyncMock,
    mock_serial_bridge_config_entry: MockConfigEntry,
) -> None:
    """Test humidifier set status service."""

    await setup_integration(hass, mock_serial_bridge_config_entry)

    assert (state := hass.states.get(ENTITY_ID))
    assert state.state == STATE_ON
    assert state.attributes[ATTR_HUMIDITY] == 50.0

    # Test turn off
    await hass.services.async_call(
        HUMIDIFIER_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )
    mock_serial_bridge.set_humidity_status.assert_called()

    assert (state := hass.states.get(ENTITY_ID))
    assert state.state == STATE_OFF

    # Test turn on
    await hass.services.async_call(
        HUMIDIFIER_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )
    mock_serial_bridge.set_humidity_status.assert_called()

    assert (state := hass.states.get(ENTITY_ID))
    assert state.state == STATE_ON