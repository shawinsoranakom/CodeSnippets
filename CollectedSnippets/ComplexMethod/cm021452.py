async def test_toggle_cover(hass: HomeAssistant) -> None:
    """Test toggling the cover."""
    # Start open
    await hass.services.async_call(
        COVER_DOMAIN, SERVICE_OPEN_COVER, {ATTR_ENTITY_ID: ENTITY_COVER}, blocking=True
    )
    for _ in range(7):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

    state = hass.states.get(ENTITY_COVER)
    assert state.state == CoverState.OPEN
    assert state.attributes["current_position"] == 100
    # Toggle closed
    await hass.services.async_call(
        COVER_DOMAIN, SERVICE_TOGGLE, {ATTR_ENTITY_ID: ENTITY_COVER}, blocking=True
    )
    for _ in range(10):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

    state = hass.states.get(ENTITY_COVER)
    assert state.state == CoverState.CLOSED
    assert state.attributes[ATTR_CURRENT_POSITION] == 0
    # Toggle open
    await hass.services.async_call(
        COVER_DOMAIN, SERVICE_TOGGLE, {ATTR_ENTITY_ID: ENTITY_COVER}, blocking=True
    )
    for _ in range(10):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

    state = hass.states.get(ENTITY_COVER)
    assert state.state == CoverState.OPEN
    assert state.attributes[ATTR_CURRENT_POSITION] == 100