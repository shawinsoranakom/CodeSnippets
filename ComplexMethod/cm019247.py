async def test_toggle_valves(hass: HomeAssistant) -> None:
    """Test toggle valve function."""
    # Start valves in open state
    await hass.services.async_call(
        VALVE_DOMAIN, SERVICE_OPEN_VALVE, {ATTR_ENTITY_ID: VALVE_GROUP}, blocking=True
    )
    for _ in range(10):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

    state = hass.states.get(VALVE_GROUP)
    assert state.state == ValveState.OPEN

    # Toggle will close valves
    await hass.services.async_call(
        VALVE_DOMAIN, SERVICE_TOGGLE, {ATTR_ENTITY_ID: VALVE_GROUP}, blocking=True
    )
    for _ in range(10):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

    state = hass.states.get(VALVE_GROUP)
    assert state.state == ValveState.CLOSED
    assert state.attributes[ATTR_CURRENT_POSITION] == 0

    assert hass.states.get(DEMO_VALVE1).state == ValveState.CLOSED
    assert hass.states.get(DEMO_VALVE_POS1).attributes[ATTR_CURRENT_POSITION] == 0
    assert hass.states.get(DEMO_VALVE_POS2).attributes[ATTR_CURRENT_POSITION] == 0

    # Toggle again will open valves
    await hass.services.async_call(
        VALVE_DOMAIN, SERVICE_TOGGLE, {ATTR_ENTITY_ID: VALVE_GROUP}, blocking=True
    )
    for _ in range(10):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

    state = hass.states.get(VALVE_GROUP)
    assert state.state == ValveState.OPEN
    assert state.attributes[ATTR_CURRENT_POSITION] == 100

    assert hass.states.get(DEMO_VALVE1).state == ValveState.OPEN
    assert hass.states.get(DEMO_VALVE_POS1).attributes[ATTR_CURRENT_POSITION] == 100
    assert hass.states.get(DEMO_VALVE_POS2).attributes[ATTR_CURRENT_POSITION] == 100