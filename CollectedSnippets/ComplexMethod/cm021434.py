async def test_set_valve_position(hass: HomeAssistant) -> None:
    """Test moving the valve to a specific position."""
    state = hass.states.get(BACK_GARDEN)
    assert state is not None
    assert state.attributes[ATTR_CURRENT_POSITION] == 70

    # close to 10%
    await hass.services.async_call(
        VALVE_DOMAIN,
        SERVICE_SET_VALVE_POSITION,
        {ATTR_ENTITY_ID: BACK_GARDEN, ATTR_POSITION: 10},
        blocking=True,
    )
    state = hass.states.get(BACK_GARDEN)
    assert state is not None
    assert state.state == ValveState.CLOSING

    for _ in range(6):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

    state = hass.states.get(BACK_GARDEN)
    assert state is not None
    assert state.attributes[ATTR_CURRENT_POSITION] == 10
    assert state.state == ValveState.OPEN

    # open to 80%
    await hass.services.async_call(
        VALVE_DOMAIN,
        SERVICE_SET_VALVE_POSITION,
        {ATTR_ENTITY_ID: BACK_GARDEN, ATTR_POSITION: 80},
        blocking=True,
    )
    state = hass.states.get(BACK_GARDEN)
    assert state is not None
    assert state.state == ValveState.OPENING

    for _ in range(7):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

    state = hass.states.get(BACK_GARDEN)
    assert state is not None
    assert state.attributes[ATTR_CURRENT_POSITION] == 80
    assert state.state == ValveState.OPEN

    # test valve is at requested position
    state_changes = async_capture_events(hass, EVENT_STATE_CHANGED)
    await hass.services.async_call(
        VALVE_DOMAIN,
        SERVICE_SET_VALVE_POSITION,
        {ATTR_ENTITY_ID: BACK_GARDEN, ATTR_POSITION: 80},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(state_changes) == 0