async def test_set_cover_position(hass: HomeAssistant) -> None:
    """Test moving the cover to a specific position."""
    state = hass.states.get(ENTITY_COVER)
    assert state.attributes[ATTR_CURRENT_POSITION] == 70

    # close to 10%
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_SET_COVER_POSITION,
        {ATTR_ENTITY_ID: ENTITY_COVER, ATTR_POSITION: 10},
        blocking=True,
    )
    state = hass.states.get(ENTITY_COVER)
    assert state.state == CoverState.CLOSING

    for _ in range(6):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

    state = hass.states.get(ENTITY_COVER)
    assert state.attributes[ATTR_CURRENT_POSITION] == 10
    assert state.state == CoverState.OPEN

    # open to 80%
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_SET_COVER_POSITION,
        {ATTR_ENTITY_ID: ENTITY_COVER, ATTR_POSITION: 80},
        blocking=True,
    )
    state = hass.states.get(ENTITY_COVER)
    assert state.state == CoverState.OPENING

    for _ in range(7):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

    state = hass.states.get(ENTITY_COVER)
    assert state.attributes[ATTR_CURRENT_POSITION] == 80
    assert state.state == CoverState.OPEN