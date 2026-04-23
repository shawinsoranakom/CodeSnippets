async def test_open_close_cover_state(
    hass: HomeAssistant, dummy_device_from_host_cover
) -> None:
    """Test the change of state of the cover."""
    await setup_integration(hass)

    # Open
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER,
        {ATTR_ENTITY_ID: "cover.wl000000000099_1"},
        blocking=True,
    )

    await hass.async_block_till_done()
    state = hass.states.get("cover.wl000000000099_1")
    assert state
    assert state.state == CoverState.OPENING

    # Close
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER,
        {ATTR_ENTITY_ID: "cover.wl000000000099_1"},
        blocking=True,
    )

    await hass.async_block_till_done()
    state = hass.states.get("cover.wl000000000099_1")
    assert state
    assert state.state == CoverState.CLOSING

    # Set position
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_SET_COVER_POSITION,
        {ATTR_POSITION: 50, ATTR_ENTITY_ID: "cover.wl000000000099_1"},
        blocking=True,
    )

    await hass.async_block_till_done()
    state = hass.states.get("cover.wl000000000099_1")
    assert state
    assert state.state == CoverState.OPEN
    assert state.attributes.get(ATTR_CURRENT_POSITION) == 50

    # Stop
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_STOP_COVER,
        {ATTR_ENTITY_ID: "cover.wl000000000099_1"},
        blocking=True,
    )

    await hass.async_block_till_done()
    state = hass.states.get("cover.wl000000000099_1")
    assert state
    assert state.state == CoverState.OPEN