async def test_toggle_covers(hass: HomeAssistant) -> None:
    """Test toggle cover function."""
    # Start covers in open state
    await hass.services.async_call(
        COVER_DOMAIN, SERVICE_OPEN_COVER, {ATTR_ENTITY_ID: COVER_GROUP}, blocking=True
    )
    for _ in range(10):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

    state = hass.states.get(COVER_GROUP)
    assert state.state == CoverState.OPEN

    # Toggle will close covers
    await hass.services.async_call(
        COVER_DOMAIN, SERVICE_TOGGLE, {ATTR_ENTITY_ID: COVER_GROUP}, blocking=True
    )
    for _ in range(10):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

    state = hass.states.get(COVER_GROUP)
    assert state.state == CoverState.CLOSED
    assert state.attributes[ATTR_CURRENT_POSITION] == 0

    assert hass.states.get(DEMO_COVER).state == CoverState.CLOSED
    assert hass.states.get(DEMO_COVER_POS).attributes[ATTR_CURRENT_POSITION] == 0
    assert hass.states.get(DEMO_COVER_TILT).attributes[ATTR_CURRENT_POSITION] == 0

    # Toggle again will open covers
    await hass.services.async_call(
        COVER_DOMAIN, SERVICE_TOGGLE, {ATTR_ENTITY_ID: COVER_GROUP}, blocking=True
    )
    for _ in range(10):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

    state = hass.states.get(COVER_GROUP)
    assert state.state == CoverState.OPEN
    assert state.attributes[ATTR_CURRENT_POSITION] == 100

    assert hass.states.get(DEMO_COVER).state == CoverState.OPEN
    assert hass.states.get(DEMO_COVER_POS).attributes[ATTR_CURRENT_POSITION] == 100
    assert hass.states.get(DEMO_COVER_TILT).attributes[ATTR_CURRENT_POSITION] == 100