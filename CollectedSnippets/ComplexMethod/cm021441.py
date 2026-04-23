async def test_state_attributes(hass: HomeAssistant) -> None:
    """Test light state attributes."""
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY_LIGHT, ATTR_XY_COLOR: (0.4, 0.4), ATTR_BRIGHTNESS: 25},
        blocking=True,
    )

    state = hass.states.get(ENTITY_LIGHT)
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_XY_COLOR) == (0.4, 0.4)
    assert state.attributes.get(ATTR_BRIGHTNESS) == 25
    assert state.attributes.get(ATTR_RGB_COLOR) == (255, 234, 164)
    assert state.attributes.get(ATTR_EFFECT) == "rainbow"

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: ENTITY_LIGHT,
            ATTR_RGB_COLOR: (251, 253, 255),
        },
        blocking=True,
    )

    state = hass.states.get(ENTITY_LIGHT)
    assert state.attributes.get(ATTR_RGB_COLOR) == (251, 253, 255)
    assert state.attributes.get(ATTR_XY_COLOR) == (0.319, 0.327)

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: ENTITY_LIGHT,
            ATTR_EFFECT: "off",
            ATTR_COLOR_TEMP_KELVIN: 2500,
        },
        blocking=True,
    )

    state = hass.states.get(ENTITY_LIGHT)
    assert state.attributes.get(ATTR_COLOR_TEMP_KELVIN) == 2500
    assert state.attributes.get(ATTR_MAX_COLOR_TEMP_KELVIN) == 6535
    assert state.attributes.get(ATTR_MIN_COLOR_TEMP_KELVIN) == 2000
    assert state.attributes.get(ATTR_EFFECT) == "off"

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: ENTITY_LIGHT,
            ATTR_BRIGHTNESS_PCT: 50,
            ATTR_COLOR_TEMP_KELVIN: 3000,
        },
        blocking=True,
    )

    state = hass.states.get(ENTITY_LIGHT)
    assert state.attributes.get(ATTR_COLOR_TEMP_KELVIN) == 3000
    assert state.attributes.get(ATTR_BRIGHTNESS) == 128