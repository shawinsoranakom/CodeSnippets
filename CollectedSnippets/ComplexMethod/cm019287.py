async def test_emulated_color_temp_group(hass: HomeAssistant) -> None:
    """Test emulated color temperature in a group."""
    entities = [
        MockLight("test1", STATE_ON),
        MockLight("test2", STATE_OFF),
        MockLight("test3", STATE_OFF),
    ]
    setup_test_component_platform(hass, LIGHT_DOMAIN, entities)

    entity0 = entities[0]
    entity0.supported_color_modes = {ColorMode.COLOR_TEMP}
    entity0.color_mode = ColorMode.COLOR_TEMP

    entity1 = entities[1]
    entity1.supported_color_modes = {ColorMode.COLOR_TEMP, ColorMode.HS}
    entity1.color_mode = ColorMode.COLOR_TEMP

    entity2 = entities[2]
    entity2.supported_color_modes = {ColorMode.HS}
    entity2.color_mode = ColorMode.HS

    assert await async_setup_component(
        hass,
        LIGHT_DOMAIN,
        {
            LIGHT_DOMAIN: [
                {"platform": "test"},
                {
                    "platform": DOMAIN,
                    "entities": ["light.test1", "light.test2", "light.test3"],
                    "all": "false",
                },
            ]
        },
    )

    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()

    await hass.async_block_till_done()
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "light.light_group", ATTR_COLOR_TEMP_KELVIN: 5000},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get("light.test1")
    assert state.state == STATE_ON
    assert state.attributes[ATTR_COLOR_TEMP_KELVIN] == 5000
    assert ATTR_HS_COLOR in state.attributes

    state = hass.states.get("light.test2")
    assert state.state == STATE_ON
    assert state.attributes[ATTR_COLOR_TEMP_KELVIN] == 5000
    assert ATTR_HS_COLOR in state.attributes

    state = hass.states.get("light.test3")
    assert state.state == STATE_ON
    assert state.attributes[ATTR_HS_COLOR] == (27.001, 19.243)