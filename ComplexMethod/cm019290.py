async def test_service_call_effect(hass: HomeAssistant) -> None:
    """Test service calls."""
    await async_setup_component(
        hass,
        LIGHT_DOMAIN,
        {
            LIGHT_DOMAIN: [
                {"platform": "demo"},
                {
                    "platform": DOMAIN,
                    "entities": [
                        "light.bed_light",
                        "light.ceiling_lights",
                        "light.kitchen_lights",
                    ],
                    "all": "false",
                },
            ]
        },
    )
    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()

    assert hass.states.get("light.light_group").state == STATE_ON

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: "light.light_group",
            ATTR_BRIGHTNESS: 128,
            ATTR_EFFECT: "Random",
            ATTR_RGB_COLOR: (42, 255, 255),
        },
        blocking=True,
    )

    state = hass.states.get("light.bed_light")
    assert state.state == STATE_ON
    assert state.attributes[ATTR_BRIGHTNESS] == 128
    assert state.attributes[ATTR_EFFECT] == "Random"
    assert state.attributes[ATTR_RGB_COLOR] == (42, 255, 255)

    state = hass.states.get("light.ceiling_lights")
    assert state.state == STATE_ON
    assert state.attributes[ATTR_BRIGHTNESS] == 128
    assert state.attributes[ATTR_RGB_COLOR] == (42, 255, 255)

    state = hass.states.get("light.kitchen_lights")
    assert state.state == STATE_ON
    assert state.attributes[ATTR_BRIGHTNESS] == 128
    assert state.attributes[ATTR_RGB_COLOR] == (42, 255, 255)