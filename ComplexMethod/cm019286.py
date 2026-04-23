async def test_color_temp(hass: HomeAssistant) -> None:
    """Test color temp reporting."""
    entities = [
        MockLight("test1", STATE_ON),
        MockLight("test2", STATE_OFF),
    ]
    setup_test_component_platform(hass, LIGHT_DOMAIN, entities)

    entity0 = entities[0]
    entity0.supported_color_modes = {ColorMode.COLOR_TEMP}
    entity0.color_mode = ColorMode.COLOR_TEMP
    entity0.brightness = 255
    entity0.color_temp_kelvin = 2

    entity1 = entities[1]
    entity1.supported_color_modes = {ColorMode.COLOR_TEMP}
    entity1.color_mode = ColorMode.COLOR_TEMP

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

    state = hass.states.get("light.light_group")
    assert state.attributes[ATTR_COLOR_MODE] == "color_temp"
    assert state.attributes[ATTR_COLOR_TEMP_KELVIN] == 2
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0
    assert state.attributes[ATTR_SUPPORTED_COLOR_MODES] == ["color_temp"]

    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": [entity1.entity_id], ATTR_COLOR_TEMP_KELVIN: 1000},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get("light.light_group")
    assert state.attributes[ATTR_COLOR_MODE] == "color_temp"
    assert state.attributes[ATTR_COLOR_TEMP_KELVIN] == 501
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0
    assert state.attributes[ATTR_SUPPORTED_COLOR_MODES] == ["color_temp"]

    await hass.services.async_call(
        "light",
        "turn_off",
        {"entity_id": [entity0.entity_id]},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get("light.light_group")
    assert state.attributes[ATTR_COLOR_MODE] == "color_temp"
    assert state.attributes[ATTR_COLOR_TEMP_KELVIN] == 1000
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0
    assert state.attributes[ATTR_SUPPORTED_COLOR_MODES] == ["color_temp"]