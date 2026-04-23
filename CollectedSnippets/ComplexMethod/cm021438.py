async def test_turning_off_and_on(hass: HomeAssistant) -> None:
    """Test turn_on and turn_off."""
    assert await async_setup_component(
        hass, MP_DOMAIN, {"media_player": {"platform": "demo"}}
    )
    await hass.async_block_till_done()

    state = hass.states.get(TEST_ENTITY_ID)
    assert state.state == STATE_PLAYING

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: TEST_ENTITY_ID},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(TEST_ENTITY_ID)
    assert state.state == STATE_OFF
    assert not is_on(hass, TEST_ENTITY_ID)

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: TEST_ENTITY_ID},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(TEST_ENTITY_ID)
    assert state.state == STATE_PLAYING
    assert is_on(hass, TEST_ENTITY_ID)

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_TOGGLE,
        {ATTR_ENTITY_ID: TEST_ENTITY_ID},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(TEST_ENTITY_ID)
    assert state.state == STATE_OFF
    assert not is_on(hass, TEST_ENTITY_ID)