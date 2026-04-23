async def test_is_opening_closing(hass: HomeAssistant) -> None:
    """Test is_opening property."""
    await hass.services.async_call(
        COVER_DOMAIN, SERVICE_OPEN_COVER, {ATTR_ENTITY_ID: COVER_GROUP}, blocking=True
    )
    await hass.async_block_till_done()

    # Both covers opening -> opening
    assert hass.states.get(DEMO_COVER_POS).state == CoverState.OPENING
    assert hass.states.get(DEMO_COVER_TILT).state == CoverState.OPENING
    assert hass.states.get(COVER_GROUP).state == CoverState.OPENING

    for _ in range(10):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

    await hass.services.async_call(
        COVER_DOMAIN, SERVICE_CLOSE_COVER, {ATTR_ENTITY_ID: COVER_GROUP}, blocking=True
    )

    # Both covers closing -> closing
    assert hass.states.get(DEMO_COVER_POS).state == CoverState.CLOSING
    assert hass.states.get(DEMO_COVER_TILT).state == CoverState.CLOSING
    assert hass.states.get(COVER_GROUP).state == CoverState.CLOSING

    hass.states.async_set(
        DEMO_COVER_POS, CoverState.OPENING, {ATTR_SUPPORTED_FEATURES: 11}
    )
    await hass.async_block_till_done()

    # Closing + Opening -> Opening
    assert hass.states.get(DEMO_COVER_TILT).state == CoverState.CLOSING
    assert hass.states.get(DEMO_COVER_POS).state == CoverState.OPENING
    assert hass.states.get(COVER_GROUP).state == CoverState.OPENING

    hass.states.async_set(
        DEMO_COVER_POS, CoverState.CLOSING, {ATTR_SUPPORTED_FEATURES: 11}
    )
    await hass.async_block_till_done()

    # Both covers closing -> closing
    assert hass.states.get(DEMO_COVER_TILT).state == CoverState.CLOSING
    assert hass.states.get(DEMO_COVER_POS).state == CoverState.CLOSING
    assert hass.states.get(COVER_GROUP).state == CoverState.CLOSING

    # Closed + Closing -> Closing
    hass.states.async_set(
        DEMO_COVER_POS, CoverState.CLOSED, {ATTR_SUPPORTED_FEATURES: 11}
    )
    await hass.async_block_till_done()
    assert hass.states.get(DEMO_COVER_TILT).state == CoverState.CLOSING
    assert hass.states.get(DEMO_COVER_POS).state == CoverState.CLOSED
    assert hass.states.get(COVER_GROUP).state == CoverState.CLOSING

    # Open + Closing -> Closing
    hass.states.async_set(
        DEMO_COVER_POS, CoverState.OPEN, {ATTR_SUPPORTED_FEATURES: 11}
    )
    await hass.async_block_till_done()
    assert hass.states.get(DEMO_COVER_TILT).state == CoverState.CLOSING
    assert hass.states.get(DEMO_COVER_POS).state == CoverState.OPEN
    assert hass.states.get(COVER_GROUP).state == CoverState.CLOSING

    # Closed + Opening -> Closing
    hass.states.async_set(
        DEMO_COVER_TILT, CoverState.OPENING, {ATTR_SUPPORTED_FEATURES: 11}
    )
    hass.states.async_set(
        DEMO_COVER_POS, CoverState.CLOSED, {ATTR_SUPPORTED_FEATURES: 11}
    )
    await hass.async_block_till_done()
    assert hass.states.get(DEMO_COVER_TILT).state == CoverState.OPENING
    assert hass.states.get(DEMO_COVER_POS).state == CoverState.CLOSED
    assert hass.states.get(COVER_GROUP).state == CoverState.OPENING

    # Open + Opening -> Closing
    hass.states.async_set(
        DEMO_COVER_POS, CoverState.OPEN, {ATTR_SUPPORTED_FEATURES: 11}
    )
    await hass.async_block_till_done()
    assert hass.states.get(DEMO_COVER_TILT).state == CoverState.OPENING
    assert hass.states.get(DEMO_COVER_POS).state == CoverState.OPEN
    assert hass.states.get(COVER_GROUP).state == CoverState.OPENING