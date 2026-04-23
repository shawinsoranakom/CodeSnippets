async def test_mode_change_humidifier_trigger_on_not_long_enough(
    hass: HomeAssistant,
) -> None:
    """Test if mode change turns humidifier on despite minimum cycle."""
    calls = await _setup_switch(hass, False)
    _setup_sensor(hass, 45)
    await hass.async_block_till_done()
    assert len(calls) == 0

    await hass.services.async_call(
        HUMIDIFIER_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert len(calls) == 0

    _setup_sensor(hass, 35)
    await hass.async_block_till_done()
    assert len(calls) == 0

    await hass.services.async_call(
        HUMIDIFIER_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert len(calls) == 1
    call = calls[0]
    assert call.domain == "homeassistant"
    assert call.service == SERVICE_TURN_ON
    assert call.data["entity_id"] == ENT_SWITCH