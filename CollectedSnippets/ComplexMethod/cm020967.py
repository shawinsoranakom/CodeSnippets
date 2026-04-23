async def test_humidifier_set_humidity_while_off(
    hass: HomeAssistant,
    mock_serial_bridge: AsyncMock,
    mock_serial_bridge_config_entry: MockConfigEntry,
) -> None:
    """Test humidifier set humidity service while off."""

    await setup_integration(hass, mock_serial_bridge_config_entry)

    assert (state := hass.states.get(ENTITY_ID))
    assert state.state == STATE_ON
    assert state.attributes[ATTR_HUMIDITY] == 50.0

    # Switch humidifier off
    await hass.services.async_call(
        HUMIDIFIER_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )
    mock_serial_bridge.set_humidity_status.assert_called()

    assert (state := hass.states.get(ENTITY_ID))
    assert state.state == STATE_OFF

    # Try setting humidity
    with pytest.raises(HomeAssistantError) as exc_info:
        await hass.services.async_call(
            HUMIDIFIER_DOMAIN,
            SERVICE_SET_HUMIDITY,
            {ATTR_ENTITY_ID: ENTITY_ID, ATTR_HUMIDITY: 23},
            blocking=True,
        )
    assert exc_info.value.translation_domain == DOMAIN
    assert exc_info.value.translation_key == "humidity_while_off"