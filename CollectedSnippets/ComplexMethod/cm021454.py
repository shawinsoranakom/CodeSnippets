async def test_turn_on_with_speed_and_percentage(
    hass: HomeAssistant, fan_entity_id
) -> None:
    """Test turning on the device."""
    state = hass.states.get(fan_entity_id)
    assert state.state == STATE_OFF
    await hass.services.async_call(
        fan.DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_PERCENTAGE: 100},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(fan_entity_id)
    assert state.state == STATE_ON
    assert state.attributes[fan.ATTR_PERCENTAGE] == 100

    await hass.services.async_call(
        fan.DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_PERCENTAGE: 66},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(fan_entity_id)
    assert state.state == STATE_ON
    assert state.attributes[fan.ATTR_PERCENTAGE] == 66

    await hass.services.async_call(
        fan.DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_PERCENTAGE: 33},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(fan_entity_id)
    assert state.state == STATE_ON
    assert state.attributes[fan.ATTR_PERCENTAGE] == 33

    await hass.services.async_call(
        fan.DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_PERCENTAGE: 100},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(fan_entity_id)
    assert state.state == STATE_ON
    assert state.attributes[fan.ATTR_PERCENTAGE] == 100

    await hass.services.async_call(
        fan.DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_PERCENTAGE: 66},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(fan_entity_id)
    assert state.state == STATE_ON
    assert state.attributes[fan.ATTR_PERCENTAGE] == 66

    await hass.services.async_call(
        fan.DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_PERCENTAGE: 33},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(fan_entity_id)
    assert state.state == STATE_ON
    assert state.attributes[fan.ATTR_PERCENTAGE] == 33

    await hass.services.async_call(
        fan.DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_PERCENTAGE: 0},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(fan_entity_id)
    assert state.state == STATE_OFF
    assert state.attributes[fan.ATTR_PERCENTAGE] == 0