async def test_increase_decrease_speed(hass: HomeAssistant, fan_entity_id) -> None:
    """Test increasing and decreasing the percentage speed of the device."""
    state = hass.states.get(fan_entity_id)
    assert state.state == STATE_OFF
    assert state.attributes[fan.ATTR_PERCENTAGE_STEP] == 100 / 3

    await hass.services.async_call(
        fan.DOMAIN,
        fan.SERVICE_INCREASE_SPEED,
        {ATTR_ENTITY_ID: fan_entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(fan_entity_id)
    assert state.attributes[fan.ATTR_PERCENTAGE] == 33

    await hass.services.async_call(
        fan.DOMAIN,
        fan.SERVICE_INCREASE_SPEED,
        {ATTR_ENTITY_ID: fan_entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(fan_entity_id)
    assert state.attributes[fan.ATTR_PERCENTAGE] == 66

    await hass.services.async_call(
        fan.DOMAIN,
        fan.SERVICE_INCREASE_SPEED,
        {ATTR_ENTITY_ID: fan_entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(fan_entity_id)
    assert state.attributes[fan.ATTR_PERCENTAGE] == 100

    await hass.services.async_call(
        fan.DOMAIN,
        fan.SERVICE_INCREASE_SPEED,
        {ATTR_ENTITY_ID: fan_entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(fan_entity_id)
    assert state.attributes[fan.ATTR_PERCENTAGE] == 100

    await hass.services.async_call(
        fan.DOMAIN,
        fan.SERVICE_DECREASE_SPEED,
        {ATTR_ENTITY_ID: fan_entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(fan_entity_id)
    assert state.attributes[fan.ATTR_PERCENTAGE] == 66

    await hass.services.async_call(
        fan.DOMAIN,
        fan.SERVICE_DECREASE_SPEED,
        {ATTR_ENTITY_ID: fan_entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(fan_entity_id)
    assert state.attributes[fan.ATTR_PERCENTAGE] == 33

    await hass.services.async_call(
        fan.DOMAIN,
        fan.SERVICE_DECREASE_SPEED,
        {ATTR_ENTITY_ID: fan_entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(fan_entity_id)
    assert state.attributes[fan.ATTR_PERCENTAGE] == 0

    await hass.services.async_call(
        fan.DOMAIN,
        fan.SERVICE_DECREASE_SPEED,
        {ATTR_ENTITY_ID: fan_entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(fan_entity_id)
    assert state.attributes[fan.ATTR_PERCENTAGE] == 0