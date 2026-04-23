async def test_brightness(hass: HomeAssistant) -> None:
    """Test brightness reporting."""
    entities = [
        MockLight("test1", STATE_ON),
        MockLight("test2", STATE_OFF),
    ]
    setup_test_component_platform(hass, LIGHT_DOMAIN, entities)

    entity0 = entities[0]
    entity0.supported_color_modes = {ColorMode.BRIGHTNESS}
    entity0.color_mode = ColorMode.BRIGHTNESS
    entity0.brightness = 255

    entity1 = entities[1]
    entity1.supported_color_modes = {ColorMode.BRIGHTNESS}
    entity1.color_mode = ColorMode.BRIGHTNESS

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
    assert state.state == STATE_ON
    assert state.attributes[ATTR_BRIGHTNESS] == 255
    assert state.attributes[ATTR_COLOR_MODE] == "brightness"
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0
    assert state.attributes[ATTR_SUPPORTED_COLOR_MODES] == ["brightness"]

    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": [entity1.entity_id], ATTR_BRIGHTNESS: 100},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get("light.light_group")
    assert state.state == STATE_ON
    assert state.attributes[ATTR_BRIGHTNESS] == 177
    assert state.attributes[ATTR_COLOR_MODE] == "brightness"
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0
    assert state.attributes[ATTR_SUPPORTED_COLOR_MODES] == ["brightness"]

    await hass.services.async_call(
        "light",
        "turn_off",
        {"entity_id": [entity0.entity_id]},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get("light.light_group")
    assert state.state == STATE_ON
    assert state.attributes[ATTR_BRIGHTNESS] == 100
    assert state.attributes[ATTR_COLOR_MODE] == "brightness"
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0
    assert state.attributes[ATTR_SUPPORTED_COLOR_MODES] == ["brightness"]