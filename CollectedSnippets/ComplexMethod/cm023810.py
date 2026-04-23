async def test_fan_set_percentage(hass: HomeAssistant) -> None:
    """Test setting the fan percentage."""
    device, _ = await async_setup_integration(hass, bulb_type=FAKE_DIMMABLE_FAN)

    params = INITIAL_PARAMS.copy()

    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_PERCENTAGE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_PERCENTAGE: 50},
        blocking=True,
    )
    calls = device.fan_set_state.mock_calls
    assert len(calls) == 1
    args = calls[0][2]
    assert args == {"mode": 1, "speed": 3}
    await async_push_update(hass, device, _update_params(params, state=1, **args))
    device.fan_set_state.reset_mock()
    state = hass.states.get(ENTITY_ID)
    assert state.state == STATE_ON
    assert state.attributes[ATTR_PERCENTAGE] == 50

    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_PERCENTAGE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_PERCENTAGE: 0},
        blocking=True,
    )
    calls = device.fan_turn_off.mock_calls
    assert len(calls) == 1
    await async_push_update(hass, device, _update_params(params, state=0))
    device.fan_set_state.reset_mock()
    state = hass.states.get(ENTITY_ID)
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_PERCENTAGE] == 50