async def test_service_calls(
    hass: HomeAssistant,
    supported_color_modes,
) -> None:
    """Test service calls."""
    entities = [
        MockLight("bed_light", STATE_ON),
        MockLight("ceiling_lights", STATE_OFF),
        MockLight("kitchen_lights", STATE_OFF),
    ]
    setup_test_component_platform(hass, LIGHT_DOMAIN, entities)

    entity0 = entities[0]
    entity0.supported_color_modes = {supported_color_modes}
    entity0.color_mode = supported_color_modes
    entity0.brightness = 255
    entity0.rgb_color = (0, 64, 128)

    entity1 = entities[1]
    entity1.supported_color_modes = {supported_color_modes}
    entity1.color_mode = supported_color_modes
    entity1.brightness = 255
    entity1.rgb_color = (255, 128, 64)

    entity2 = entities[2]
    entity2.supported_color_modes = {supported_color_modes}
    entity2.color_mode = supported_color_modes
    entity2.brightness = 255
    entity2.rgb_color = (255, 128, 64)

    await async_setup_component(
        hass,
        LIGHT_DOMAIN,
        {
            LIGHT_DOMAIN: [
                {"platform": "test"},
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

    group_state = hass.states.get("light.light_group")
    assert group_state.state == STATE_ON
    assert group_state.attributes[ATTR_SUPPORTED_COLOR_MODES] == [supported_color_modes]

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TOGGLE,
        {ATTR_ENTITY_ID: "light.light_group"},
        blocking=True,
    )
    assert hass.states.get("light.bed_light").state == STATE_OFF
    assert hass.states.get("light.ceiling_lights").state == STATE_OFF
    assert hass.states.get("light.kitchen_lights").state == STATE_OFF

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "light.light_group"},
        blocking=True,
    )

    assert hass.states.get("light.bed_light").state == STATE_ON
    assert hass.states.get("light.ceiling_lights").state == STATE_ON
    assert hass.states.get("light.kitchen_lights").state == STATE_ON

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "light.light_group"},
        blocking=True,
    )

    assert hass.states.get("light.bed_light").state == STATE_OFF
    assert hass.states.get("light.ceiling_lights").state == STATE_OFF
    assert hass.states.get("light.kitchen_lights").state == STATE_OFF

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: "light.light_group",
            ATTR_BRIGHTNESS: 128,
            ATTR_RGB_COLOR: (42, 255, 255),
        },
        blocking=True,
    )

    state = hass.states.get("light.bed_light")
    assert state.state == STATE_ON
    assert state.attributes[ATTR_BRIGHTNESS] == 128
    assert state.attributes[ATTR_RGB_COLOR] == (42, 255, 255)

    state = hass.states.get("light.ceiling_lights")
    assert state.state == STATE_ON
    assert state.attributes[ATTR_BRIGHTNESS] == 128
    assert state.attributes[ATTR_RGB_COLOR] == (42, 255, 255)

    state = hass.states.get("light.kitchen_lights")
    assert state.state == STATE_ON
    assert state.attributes[ATTR_BRIGHTNESS] == 128
    assert state.attributes[ATTR_RGB_COLOR] == (42, 255, 255)

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: "light.light_group",
            ATTR_BRIGHTNESS: 128,
            ATTR_COLOR_NAME: "red",
        },
        blocking=True,
    )

    state = hass.states.get("light.bed_light")
    assert state.state == STATE_ON
    assert state.attributes[ATTR_BRIGHTNESS] == 128
    assert state.attributes[ATTR_RGB_COLOR] == (255, 0, 0)

    state = hass.states.get("light.ceiling_lights")
    assert state.state == STATE_ON
    assert state.attributes[ATTR_BRIGHTNESS] == 128
    assert state.attributes[ATTR_RGB_COLOR] == (255, 0, 0)

    state = hass.states.get("light.kitchen_lights")
    assert state.state == STATE_ON
    assert state.attributes[ATTR_BRIGHTNESS] == 128
    assert state.attributes[ATTR_RGB_COLOR] == (255, 0, 0)