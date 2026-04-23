async def test_pump(hass: HomeAssistant, client: MagicMock, mock_pump) -> None:
    """Test spa pump."""
    await init_integration(hass)

    # check if the initial state is off
    state = hass.states.get(ENTITY_FAN)
    assert state.state == STATE_OFF

    # just call turn on, pump should be at full speed
    await common.async_turn_on(hass, ENTITY_FAN)
    state = await client_update(hass, client, ENTITY_FAN)
    assert state.state == STATE_ON
    assert state.attributes[ATTR_PERCENTAGE] == 100

    # test setting percentage
    await common.async_set_percentage(hass, ENTITY_FAN, 50)
    state = await client_update(hass, client, ENTITY_FAN)
    assert state.state == STATE_ON
    assert state.attributes[ATTR_PERCENTAGE] == 50

    # test calling turn off
    await common.async_turn_off(hass, ENTITY_FAN)
    state = await client_update(hass, client, ENTITY_FAN)
    assert state.state == STATE_OFF

    # test setting percentage to 0
    await common.async_turn_on(hass, ENTITY_FAN)
    await client_update(hass, client, ENTITY_FAN)

    await common.async_set_percentage(hass, ENTITY_FAN, 0)
    state = await client_update(hass, client, ENTITY_FAN)
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_PERCENTAGE] == 0