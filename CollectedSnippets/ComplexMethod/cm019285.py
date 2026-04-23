async def test_white(hass: HomeAssistant) -> None:
    """Test white reporting."""
    entities = [
        MockLight("test1", STATE_ON),
        MockLight("test2", STATE_ON),
    ]
    setup_test_component_platform(hass, LIGHT_DOMAIN, entities)

    entity0 = entities[0]
    entity0.supported_color_modes = {ColorMode.HS, ColorMode.WHITE}
    entity0.color_mode = ColorMode.WHITE
    entity0.brightness = 255

    entity1 = entities[1]
    entity1.supported_color_modes = {ColorMode.HS, ColorMode.WHITE}
    entity1.color_mode = ColorMode.WHITE
    entity1.brightness = 128

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
    assert state.attributes[ATTR_COLOR_MODE] == "white"
    assert state.attributes[ATTR_BRIGHTNESS] == 191
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0
    assert state.attributes[ATTR_SUPPORTED_COLOR_MODES] == ["hs", "white"]

    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": ["light.light_group"], ATTR_WHITE: 128},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get("light.light_group")
    assert state.attributes[ATTR_COLOR_MODE] == "white"
    assert state.attributes[ATTR_BRIGHTNESS] == 128
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0
    assert state.attributes[ATTR_SUPPORTED_COLOR_MODES] == ["hs", "white"]