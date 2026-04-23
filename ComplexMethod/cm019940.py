async def test_light_service_call_color_temp_conversion(hass: HomeAssistant) -> None:
    """Test color temp conversion in service calls."""
    entities = [
        MockLight("Test_rgbww_ct", STATE_ON),
        MockLight("Test_rgbww", STATE_ON),
    ]
    setup_test_component_platform(hass, light.DOMAIN, entities)

    entity0 = entities[0]
    entity0.supported_color_modes = {
        light.ColorMode.COLOR_TEMP,
        light.ColorMode.RGBWW,
    }
    entity0.color_mode = light.ColorMode.COLOR_TEMP

    entity1 = entities[1]
    entity1.supported_color_modes = {light.ColorMode.RGBWW}
    entity1.color_mode = light.ColorMode.RGBWW
    assert entity1.min_color_temp_kelvin == 2000
    assert entity1.max_color_temp_kelvin == 6535

    assert await async_setup_component(hass, "light", {"light": {"platform": "test"}})
    await hass.async_block_till_done()

    state = hass.states.get(entity0.entity_id)
    assert state.attributes["supported_color_modes"] == [
        light.ColorMode.COLOR_TEMP,
        light.ColorMode.RGBWW,
    ]
    assert state.attributes["min_color_temp_kelvin"] == 2000
    assert state.attributes["max_color_temp_kelvin"] == 6535

    state = hass.states.get(entity1.entity_id)
    assert state.attributes["supported_color_modes"] == [light.ColorMode.RGBWW]

    await hass.services.async_call(
        "light",
        "turn_on",
        {
            "entity_id": [
                entity0.entity_id,
                entity1.entity_id,
            ],
            "brightness_pct": 100,
            "color_temp_kelvin": 6535,
        },
        blocking=True,
    )
    _, data = entity0.last_call("turn_on")
    assert data == {"brightness": 255, "color_temp_kelvin": 6535}
    _, data = entity1.last_call("turn_on")
    # Home Assistant uses RGBCW so a mireds of 153 should be maximum cold at 100% brightness so 255
    assert data == {"brightness": 255, "rgbww_color": (0, 0, 0, 255, 0)}

    await hass.services.async_call(
        "light",
        "turn_on",
        {
            "entity_id": [
                entity0.entity_id,
                entity1.entity_id,
            ],
            "brightness_pct": 50,
            "color_temp_kelvin": 2000,
        },
        blocking=True,
    )
    _, data = entity0.last_call("turn_on")
    assert data == {"brightness": 128, "color_temp_kelvin": 2000}
    _, data = entity1.last_call("turn_on")
    # Home Assistant uses RGBCW so a mireds of 500 should be maximum warm at 50% brightness so 128
    assert data == {"brightness": 128, "rgbww_color": (0, 0, 0, 0, 128)}

    await hass.services.async_call(
        "light",
        "turn_on",
        {
            "entity_id": [
                entity0.entity_id,
                entity1.entity_id,
            ],
            "brightness_pct": 100,
            "color_temp_kelvin": 3058,
        },
        blocking=True,
    )
    _, data = entity0.last_call("turn_on")
    assert data == {"brightness": 255, "color_temp_kelvin": 3058}
    _, data = entity1.last_call("turn_on")
    # Home Assistant uses RGBCW so a mireds of 328 should be the midway point at 100% brightness so 127 (rounding), 128
    assert data == {"brightness": 255, "rgbww_color": (0, 0, 0, 127, 128)}

    await hass.services.async_call(
        "light",
        "turn_on",
        {
            "entity_id": [
                entity0.entity_id,
                entity1.entity_id,
            ],
            "brightness_pct": 100,
            "color_temp_kelvin": 4166,
        },
        blocking=True,
    )
    _, data = entity0.last_call("turn_on")
    assert data == {"brightness": 255, "color_temp_kelvin": 4166}
    _, data = entity1.last_call("turn_on")
    assert data == {"brightness": 255, "rgbww_color": (0, 0, 0, 191, 64)}

    await hass.services.async_call(
        "light",
        "turn_on",
        {
            "entity_id": [
                entity0.entity_id,
                entity1.entity_id,
            ],
            "brightness_pct": 100,
            "color_temp_kelvin": 2439,
        },
        blocking=True,
    )
    _, data = entity0.last_call("turn_on")
    assert data == {"brightness": 255, "color_temp_kelvin": 2439}
    _, data = entity1.last_call("turn_on")
    assert data == {"brightness": 255, "rgbww_color": (0, 0, 0, 66, 189)}