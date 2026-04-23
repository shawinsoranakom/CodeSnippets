async def test_light_service_turn(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
    mock_modbus,
) -> None:
    """Run test for service turn_on/turn_off."""

    assert DOMAIN in hass.config.components
    assert hass.states.get(ENTITY_ID).state == STATE_OFF
    await hass.services.async_call(
        LIGHT_DOMAIN, SERVICE_TURN_ON, service_data={ATTR_ENTITY_ID: ENTITY_ID}
    )
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == STATE_ON
    await hass.services.async_call(
        LIGHT_DOMAIN, SERVICE_TURN_OFF, service_data={ATTR_ENTITY_ID: ENTITY_ID}
    )
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == STATE_OFF

    mock_modbus.read_holding_registers.return_value = ReadResult([0x01])
    assert hass.states.get(ENTITY_ID2).state == STATE_OFF
    await hass.services.async_call(
        LIGHT_DOMAIN, SERVICE_TURN_ON, service_data={ATTR_ENTITY_ID: ENTITY_ID2}
    )
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID2).state == STATE_ON
    mock_modbus.read_holding_registers.return_value = ReadResult([0x00])
    await hass.services.async_call(
        LIGHT_DOMAIN, SERVICE_TURN_OFF, service_data={ATTR_ENTITY_ID: ENTITY_ID2}
    )
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID2).state == STATE_OFF

    mock_modbus.write_register.side_effect = ModbusException("fail write_")
    await hass.services.async_call(
        LIGHT_DOMAIN, SERVICE_TURN_ON, service_data={ATTR_ENTITY_ID: ENTITY_ID2}
    )
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID2).state == STATE_UNAVAILABLE