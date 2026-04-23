async def test_color_light_state(
    hass: HomeAssistant, dummy_device_from_host_color
) -> None:
    """Test the change of state of the light switches."""
    await setup_integration(hass)

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_BRIGHTNESS: 42,
            ATTR_HS_COLOR: [0, 100],
            ATTR_ENTITY_ID: "light.wl000000000099_1",
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get("light.wl000000000099_1")
    assert state
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_BRIGHTNESS) == 42
    state_color = [
        round(state.attributes.get(ATTR_HS_COLOR)[0]),
        round(state.attributes.get(ATTR_HS_COLOR)[1]),
    ]
    assert state_color == [0, 100]

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
        {
            ATTR_BRIGHTNESS: 100,
            ATTR_HS_COLOR: [270, 50],
            ATTR_ENTITY_ID: "light.wl000000000099_1",
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get("light.wl000000000099_1")
    assert state
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_BRIGHTNESS) == 100
    state_color = [
        round(state.attributes.get(ATTR_HS_COLOR)[0]),
        round(state.attributes.get(ATTR_HS_COLOR)[1]),
    ]
    assert state_color == [270, 50]

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

    # Hue = 0, Saturation = 100
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_HS_COLOR: [0, 100], ATTR_ENTITY_ID: "light.wl000000000099_1"},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get("light.wl000000000099_1")
    assert state
    assert state.state == STATE_ON
    state_color = [
        round(state.attributes.get(ATTR_HS_COLOR)[0]),
        round(state.attributes.get(ATTR_HS_COLOR)[1]),
    ]
    assert state_color == [0, 100]

    # Brightness = 60
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_BRIGHTNESS: 60, ATTR_ENTITY_ID: "light.wl000000000099_1"},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get("light.wl000000000099_1")
    assert state
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_BRIGHTNESS) == 60