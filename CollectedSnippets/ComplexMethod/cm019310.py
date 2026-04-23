async def test_toggle_tilts(hass: HomeAssistant) -> None:
    """Test toggle tilt function."""
    # Start tilted open
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER_TILT,
        {ATTR_ENTITY_ID: COVER_GROUP},
        blocking=True,
    )
    for _ in range(10):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

    state = hass.states.get(COVER_GROUP)
    assert state.state == CoverState.OPEN
    assert state.attributes[ATTR_CURRENT_TILT_POSITION] == 100

    assert (
        hass.states.get(DEMO_COVER_TILT).attributes[ATTR_CURRENT_TILT_POSITION] == 100
    )

    # Toggle will tilt closed
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_TOGGLE_COVER_TILT,
        {ATTR_ENTITY_ID: COVER_GROUP},
        blocking=True,
    )
    for _ in range(10):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

    state = hass.states.get(COVER_GROUP)
    assert state.state == CoverState.OPEN
    assert state.attributes[ATTR_CURRENT_TILT_POSITION] == 0

    assert hass.states.get(DEMO_COVER_TILT).attributes[ATTR_CURRENT_TILT_POSITION] == 0

    # Toggle again will tilt open
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_TOGGLE_COVER_TILT,
        {ATTR_ENTITY_ID: COVER_GROUP},
        blocking=True,
    )
    for _ in range(10):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

    state = hass.states.get(COVER_GROUP)
    assert state.state == CoverState.OPEN
    assert state.attributes[ATTR_CURRENT_TILT_POSITION] == 100

    assert (
        hass.states.get(DEMO_COVER_TILT).attributes[ATTR_CURRENT_TILT_POSITION] == 100
    )