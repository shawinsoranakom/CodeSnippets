async def setup_light(hass: HomeAssistant):
    """Configure our light component to work against for testing."""
    assert await async_setup_component(
        hass, LIGHT_DOMAIN, {LIGHT_DOMAIN: {"platform": "demo"}}
    )
    await hass.async_block_till_done()

    state = hass.states.get(LIGHT_ENTITY)
    assert state

    # Validate starting values
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_BRIGHTNESS) == 180
    assert state.attributes.get(ATTR_RGB_COLOR) == (255, 64, 112)

    await hass.services.async_call(
        LIGHT_DOMAIN,
        LIGHT_SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: LIGHT_ENTITY},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get(LIGHT_ENTITY)

    assert state
    assert state.state == STATE_OFF