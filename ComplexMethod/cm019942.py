async def test_light_state_color_conversion(hass: HomeAssistant) -> None:
    """Test color conversion in state updates."""
    entities = [
        MockLight("Test_hs", STATE_ON),
        MockLight("Test_rgb", STATE_ON),
        MockLight("Test_xy", STATE_ON),
    ]
    setup_test_component_platform(hass, light.DOMAIN, entities)

    entity0 = entities[0]
    entity0.supported_color_modes = {light.ColorMode.HS}
    entity0.color_mode = light.ColorMode.HS
    entity0.hs_color = (240, 100)
    entity0.rgb_color = "Invalid"  # Should be ignored
    entity0.xy_color = "Invalid"  # Should be ignored

    entity1 = entities[1]
    entity1.supported_color_modes = {light.ColorMode.RGB}
    entity1.color_mode = light.ColorMode.RGB
    entity1.hs_color = "Invalid"  # Should be ignored
    entity1.rgb_color = (128, 0, 0)
    entity1.xy_color = "Invalid"  # Should be ignored

    entity2 = entities[2]
    entity2.supported_color_modes = {light.ColorMode.XY}
    entity2.color_mode = light.ColorMode.XY
    entity2.hs_color = "Invalid"  # Should be ignored
    entity2.rgb_color = "Invalid"  # Should be ignored
    entity2.xy_color = (0.1, 0.8)

    assert await async_setup_component(hass, "light", {"light": {"platform": "test"}})
    await hass.async_block_till_done()

    state = hass.states.get(entity0.entity_id)
    assert state.attributes["color_mode"] == light.ColorMode.HS
    assert state.attributes["hs_color"] == (240, 100)
    assert state.attributes["rgb_color"] == (0, 0, 255)
    assert state.attributes["xy_color"] == (0.136, 0.04)

    state = hass.states.get(entity1.entity_id)
    assert state.attributes["color_mode"] == light.ColorMode.RGB
    assert state.attributes["hs_color"] == (0.0, 100.0)
    assert state.attributes["rgb_color"] == (128, 0, 0)
    assert state.attributes["xy_color"] == (0.701, 0.299)

    state = hass.states.get(entity2.entity_id)
    assert state.attributes["color_mode"] == light.ColorMode.XY
    assert state.attributes["hs_color"] == (125.176, 100.0)
    assert state.attributes["rgb_color"] == (0, 255, 22)
    assert state.attributes["xy_color"] == (0.1, 0.8)