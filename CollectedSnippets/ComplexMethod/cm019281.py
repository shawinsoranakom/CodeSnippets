async def test_color_hs(hass: HomeAssistant) -> None:
    """Test hs color reporting."""
    entities = [
        MockLight("test1", STATE_ON),
        MockLight("test2", STATE_OFF),
    ]
    setup_test_component_platform(hass, LIGHT_DOMAIN, entities)

    entity0 = entities[0]
    entity0.supported_color_modes = {ColorMode.HS}
    entity0.color_mode = ColorMode.HS
    entity0.brightness = 255
    entity0.hs_color = (0, 100)

    entity1 = entities[1]
    entity1.supported_color_modes = {ColorMode.HS}
    entity1.color_mode = ColorMode.HS

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
    assert state.attributes[ATTR_COLOR_MODE] == "hs"
    assert state.attributes[ATTR_HS_COLOR] == (0, 100)
    assert state.attributes[ATTR_SUPPORTED_COLOR_MODES] == ["hs"]
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0

    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": [entity1.entity_id], ATTR_HS_COLOR: (0, 50)},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get("light.light_group")
    assert state.attributes[ATTR_COLOR_MODE] == "hs"
    assert state.attributes[ATTR_HS_COLOR] == (0, 75)
    assert state.attributes[ATTR_SUPPORTED_COLOR_MODES] == ["hs"]
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0

    await hass.services.async_call(
        "light",
        "turn_off",
        {"entity_id": [entity0.entity_id]},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get("light.light_group")
    assert state.attributes[ATTR_COLOR_MODE] == "hs"
    assert state.attributes[ATTR_HS_COLOR] == (0, 50)
    assert state.attributes[ATTR_SUPPORTED_COLOR_MODES] == ["hs"]
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0

    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": [entity0.entity_id], ATTR_HS_COLOR: (355, 100)},
        blocking=True,
    )

    await hass.async_block_till_done()
    state = hass.states.get("light.light_group")
    assert state.attributes[ATTR_COLOR_MODE] == "hs"
    assert state.attributes[ATTR_HS_COLOR] == (357.5, 75)
    assert state.attributes[ATTR_SUPPORTED_COLOR_MODES] == ["hs"]
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0

    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": [entity1.entity_id], ATTR_HS_COLOR: (5, 90)},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get("light.light_group")
    assert state.attributes[ATTR_COLOR_MODE] == "hs"
    assert state.attributes[ATTR_HS_COLOR] == (360, 95)
    assert state.attributes[ATTR_SUPPORTED_COLOR_MODES] == ["hs"]
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0