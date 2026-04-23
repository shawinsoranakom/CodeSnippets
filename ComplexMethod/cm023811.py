async def test_fan_set_direction(hass: HomeAssistant) -> None:
    """Test setting the fan direction."""
    device, _ = await async_setup_integration(hass, bulb_type=FAKE_DIMMABLE_FAN)

    params = INITIAL_PARAMS.copy()

    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_DIRECTION,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_DIRECTION: DIRECTION_REVERSE},
        blocking=True,
    )
    calls = device.fan_set_state.mock_calls
    assert len(calls) == 1
    args = calls[0][2]
    assert args == {"reverse": 1}
    await async_push_update(hass, device, _update_params(params, **args))
    device.fan_set_state.reset_mock()
    state = hass.states.get(ENTITY_ID)
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_DIRECTION] == DIRECTION_REVERSE

    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_DIRECTION,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_DIRECTION: DIRECTION_FORWARD},
        blocking=True,
    )
    calls = device.fan_set_state.mock_calls
    assert len(calls) == 1
    args = calls[0][2]
    assert args == {"reverse": 0}
    await async_push_update(hass, device, _update_params(params, **args))
    device.fan_set_state.reset_mock()
    state = hass.states.get(ENTITY_ID)
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_DIRECTION] == DIRECTION_FORWARD