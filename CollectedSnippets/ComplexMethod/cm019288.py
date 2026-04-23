async def test_min_max_mireds(hass: HomeAssistant) -> None:
    """Test min/max mireds reporting.

    min/max mireds is reported both when light is on and off
    """
    entities = [
        MockLight("test1", STATE_ON),
        MockLight("test2", STATE_OFF),
    ]
    setup_test_component_platform(hass, LIGHT_DOMAIN, entities)

    entity0 = entities[0]
    entity0.supported_color_modes = {ColorMode.COLOR_TEMP}
    entity0.color_mode = ColorMode.COLOR_TEMP
    entity0.color_temp_kelvin = 2
    entity0._attr_min_color_temp_kelvin = 2
    entity0._attr_max_color_temp_kelvin = 5

    entity1 = entities[1]
    entity1.supported_color_modes = {ColorMode.COLOR_TEMP}
    entity1.color_mode = ColorMode.COLOR_TEMP
    entity1._attr_min_color_temp_kelvin = 1
    entity1._attr_max_color_temp_kelvin = 1234567890

    assert await async_setup_component(
        hass,
        LIGHT_DOMAIN,
        {
            LIGHT_DOMAIN: [
                {"platform": "test"},
                {
                    "platform": DOMAIN,
                    "entities": ["light.test1", "light.test2"],
                    "all": "false",
                },
            ]
        },
    )
    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()

    await hass.async_block_till_done()
    state = hass.states.get("light.light_group")
    assert state.attributes[ATTR_MIN_COLOR_TEMP_KELVIN] == 1
    assert state.attributes[ATTR_MAX_COLOR_TEMP_KELVIN] == 1234567890

    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": [entity0.entity_id]},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get("light.light_group")
    assert state.attributes[ATTR_MIN_COLOR_TEMP_KELVIN] == 1
    assert state.attributes[ATTR_MAX_COLOR_TEMP_KELVIN] == 1234567890

    await hass.services.async_call(
        "light",
        "turn_off",
        {"entity_id": [entity0.entity_id]},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get("light.light_group")
    assert state.attributes[ATTR_MIN_COLOR_TEMP_KELVIN] == 1
    assert state.attributes[ATTR_MAX_COLOR_TEMP_KELVIN] == 1234567890