async def test_dimmer_light_state(
    hass: HomeAssistant, dummy_device_from_host_dimmer
) -> None:
    """Test the change of state of the light switches."""
    await setup_integration(hass)

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_BRIGHTNESS: 42, ATTR_ENTITY_ID: "light.wl000000000099_1"},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get("light.wl000000000099_1")
    assert state
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_BRIGHTNESS) == 42

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_BRIGHTNESS: 0, ATTR_ENTITY_ID: "light.wl000000000099_1"},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get("light.wl000000000099_1")
    assert state
    assert state.state == STATE_OFF

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_BRIGHTNESS: 100, ATTR_ENTITY_ID: "light.wl000000000099_1"},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get("light.wl000000000099_1")
    assert state
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_BRIGHTNESS) == 100

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "light.wl000000000099_1"},
        blocking=True,
    )

    await hass.async_block_till_done()
    state = hass.states.get("light.wl000000000099_1")
    assert state
    assert state.state == STATE_OFF

    # Turn on
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "light.wl000000000099_1"},
        blocking=True,
    )

    await hass.async_block_till_done()
    state = hass.states.get("light.wl000000000099_1")
    assert state
    assert state.state == STATE_ON