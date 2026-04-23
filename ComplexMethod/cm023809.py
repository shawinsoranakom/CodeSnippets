async def test_turn_on_off(hass: HomeAssistant) -> None:
    """Test turning the fan on and off."""
    device, _ = await async_setup_integration(hass, bulb_type=FAKE_DIMMABLE_FAN)

    params = INITIAL_PARAMS.copy()

    await hass.services.async_call(
        FAN_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ENTITY_ID}, blocking=True
    )
    calls = device.fan_turn_on.mock_calls
    assert len(calls) == 1
    args = calls[0][2]
    assert args == {"mode": None, "speed": None}
    await async_push_update(hass, device, _update_params(params, state=1, **args))
    device.fan_turn_on.reset_mock()
    state = hass.states.get(ENTITY_ID)
    assert state.state == STATE_ON

    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_PRESET_MODE: PRESET_MODE_BREEZE},
        blocking=True,
    )
    calls = device.fan_turn_on.mock_calls
    assert len(calls) == 1
    args = calls[0][2]
    assert args == {"mode": 2, "speed": None}
    await async_push_update(hass, device, _update_params(params, state=1, **args))
    device.fan_turn_on.reset_mock()
    state = hass.states.get(ENTITY_ID)
    assert state.state == STATE_ON
    assert state.attributes[ATTR_PRESET_MODE] == PRESET_MODE_BREEZE

    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_PERCENTAGE: 50},
        blocking=True,
    )
    calls = device.fan_turn_on.mock_calls
    assert len(calls) == 1
    args = calls[0][2]
    assert args == {"mode": 1, "speed": 3}
    await async_push_update(hass, device, _update_params(params, state=1, **args))
    device.fan_turn_on.reset_mock()
    state = hass.states.get(ENTITY_ID)
    assert state.state == STATE_ON
    assert state.attributes[ATTR_PERCENTAGE] == 50
    assert state.attributes[ATTR_PRESET_MODE] is None

    await hass.services.async_call(
        FAN_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: ENTITY_ID}, blocking=True
    )
    calls = device.fan_turn_off.mock_calls
    assert len(calls) == 1
    await async_push_update(hass, device, _update_params(params, state=0))
    device.fan_turn_off.reset_mock()
    state = hass.states.get(ENTITY_ID)
    assert state.state == STATE_OFF