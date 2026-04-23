async def test_light_service_call_color_conversion_named_tuple(
    hass: HomeAssistant,
) -> None:
    """Test a named tuple (RGBColor) is handled correctly."""
    entities = [
        MockLight("Test_hs", STATE_ON),
        MockLight("Test_rgb", STATE_ON),
        MockLight("Test_xy", STATE_ON),
        MockLight("Test_all", STATE_ON),
        MockLight("Test_rgbw", STATE_ON),
        MockLight("Test_rgbww", STATE_ON),
    ]
    setup_test_component_platform(hass, light.DOMAIN, entities)

    entity0 = entities[0]
    entity0.supported_color_modes = {light.ColorMode.HS}

    entity1 = entities[1]
    entity1.supported_color_modes = {light.ColorMode.RGB}

    entity2 = entities[2]
    entity2.supported_color_modes = {light.ColorMode.XY}

    entity3 = entities[3]
    entity3.supported_color_modes = {
        light.ColorMode.HS,
        light.ColorMode.RGB,
        light.ColorMode.XY,
    }

    entity4 = entities[4]
    entity4.supported_color_modes = {light.ColorMode.RGBW}

    entity5 = entities[5]
    entity5.supported_color_modes = {light.ColorMode.RGBWW}

    assert await async_setup_component(hass, "light", {"light": {"platform": "test"}})
    await hass.async_block_till_done()

    await hass.services.async_call(
        "light",
        "turn_on",
        {
            "entity_id": [
                entity0.entity_id,
                entity1.entity_id,
                entity2.entity_id,
                entity3.entity_id,
                entity4.entity_id,
                entity5.entity_id,
            ],
            "brightness_pct": 25,
            "rgb_color": color_util.RGBColor(128, 0, 0),
        },
        blocking=True,
    )
    _, data = entity0.last_call("turn_on")
    assert data == {"brightness": 64, "hs_color": (0.0, 100.0)}
    _, data = entity1.last_call("turn_on")
    assert data == {"brightness": 64, "rgb_color": (128, 0, 0)}
    _, data = entity2.last_call("turn_on")
    assert data == {"brightness": 64, "xy_color": (0.701, 0.299)}
    _, data = entity3.last_call("turn_on")
    assert data == {"brightness": 64, "rgb_color": (128, 0, 0)}
    _, data = entity4.last_call("turn_on")
    assert data == {"brightness": 64, "rgbw_color": (128, 0, 0, 0)}
    _, data = entity5.last_call("turn_on")
    assert data == {"brightness": 64, "rgbww_color": (128, 0, 0, 0, 0)}