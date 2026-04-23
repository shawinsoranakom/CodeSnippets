async def test_light_service_call_color_conversion(hass: HomeAssistant) -> None:
    """Test color conversion in service calls."""
    entities = [
        MockLight("Test_hs", STATE_ON),
        MockLight("Test_rgb", STATE_ON),
        MockLight("Test_xy", STATE_ON),
        MockLight("Test_all", STATE_ON),
        MockLight("Test_rgbw", STATE_ON),
        MockLight("Test_rgbww", STATE_ON),
        MockLight("Test_temperature", STATE_ON),
    ]
    setup_test_component_platform(hass, light.DOMAIN, entities)

    entity0 = entities[0]
    entity0.supported_color_modes = {light.ColorMode.HS}
    entity0.color_mode = light.ColorMode.HS

    entity1 = entities[1]
    entity1.supported_color_modes = {light.ColorMode.RGB}
    entity1.color_mode = light.ColorMode.RGB

    entity2 = entities[2]
    entity2.supported_color_modes = {light.ColorMode.XY}
    entity2.color_mode = light.ColorMode.XY

    entity3 = entities[3]
    entity3.supported_color_modes = {
        light.ColorMode.HS,
        light.ColorMode.RGB,
        light.ColorMode.XY,
    }
    entity3.color_mode = light.ColorMode.HS

    entity4 = entities[4]
    entity4.supported_color_modes = {light.ColorMode.RGBW}
    entity4.color_mode = light.ColorMode.RGBW

    entity5 = entities[5]
    entity5.supported_color_modes = {light.ColorMode.RGBWW}
    entity5.color_mode = light.ColorMode.RGBWW

    entity6 = entities[6]
    entity6.supported_color_modes = {light.ColorMode.COLOR_TEMP}
    entity6.color_mode = light.ColorMode.COLOR_TEMP

    assert await async_setup_component(hass, "light", {"light": {"platform": "test"}})
    await hass.async_block_till_done()

    state = hass.states.get(entity0.entity_id)
    assert state.attributes["supported_color_modes"] == [light.ColorMode.HS]

    state = hass.states.get(entity1.entity_id)
    assert state.attributes["supported_color_modes"] == [light.ColorMode.RGB]

    state = hass.states.get(entity2.entity_id)
    assert state.attributes["supported_color_modes"] == [light.ColorMode.XY]

    state = hass.states.get(entity3.entity_id)
    assert state.attributes["supported_color_modes"] == [
        light.ColorMode.HS,
        light.ColorMode.RGB,
        light.ColorMode.XY,
    ]

    state = hass.states.get(entity4.entity_id)
    assert state.attributes["supported_color_modes"] == [light.ColorMode.RGBW]

    state = hass.states.get(entity5.entity_id)
    assert state.attributes["supported_color_modes"] == [light.ColorMode.RGBWW]

    state = hass.states.get(entity6.entity_id)
    assert state.attributes["supported_color_modes"] == [light.ColorMode.COLOR_TEMP]

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
                entity6.entity_id,
            ],
            "brightness_pct": 100,
            "hs_color": (240, 100),
        },
        blocking=True,
    )
    _, data = entity0.last_call("turn_on")
    assert data == {"brightness": 255, "hs_color": (240.0, 100.0)}
    _, data = entity1.last_call("turn_on")
    assert data == {"brightness": 255, "rgb_color": (0, 0, 255)}
    _, data = entity2.last_call("turn_on")
    assert data == {"brightness": 255, "xy_color": (0.136, 0.04)}
    _, data = entity3.last_call("turn_on")
    assert data == {"brightness": 255, "hs_color": (240.0, 100.0)}
    _, data = entity4.last_call("turn_on")
    assert data == {"brightness": 255, "rgbw_color": (0, 0, 255, 0)}
    _, data = entity5.last_call("turn_on")
    assert data == {"brightness": 255, "rgbww_color": (0, 0, 255, 0, 0)}
    _, data = entity6.last_call("turn_on")
    assert data == {"brightness": 255, "color_temp_kelvin": 1739}

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
                entity6.entity_id,
            ],
            "brightness_pct": 100,
            "hs_color": (240, 0),
        },
        blocking=True,
    )
    _, data = entity0.last_call("turn_on")
    assert data == {"brightness": 255, "hs_color": (240.0, 0.0)}
    _, data = entity1.last_call("turn_on")
    assert data == {"brightness": 255, "rgb_color": (255, 255, 255)}
    _, data = entity2.last_call("turn_on")
    assert data == {"brightness": 255, "xy_color": (0.323, 0.329)}
    _, data = entity3.last_call("turn_on")
    assert data == {"brightness": 255, "hs_color": (240.0, 0.0)}
    _, data = entity4.last_call("turn_on")
    assert data == {"brightness": 255, "rgbw_color": (0, 0, 0, 255)}
    _, data = entity5.last_call("turn_on")
    # The midpoint of the white channels is warm, compensated by adding green + blue
    assert data == {"brightness": 255, "rgbww_color": (0, 76, 141, 255, 255)}
    _, data = entity6.last_call("turn_on")
    assert data == {"brightness": 255, "color_temp_kelvin": 5962}

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
                entity6.entity_id,
            ],
            "brightness_pct": 50,
            "rgb_color": (128, 0, 0),
        },
        blocking=True,
    )
    _, data = entity0.last_call("turn_on")
    assert data == {"brightness": 128, "hs_color": (0.0, 100.0)}
    _, data = entity1.last_call("turn_on")
    assert data == {"brightness": 128, "rgb_color": (128, 0, 0)}
    _, data = entity2.last_call("turn_on")
    assert data == {"brightness": 128, "xy_color": (0.701, 0.299)}
    _, data = entity3.last_call("turn_on")
    assert data == {"brightness": 128, "rgb_color": (128, 0, 0)}
    _, data = entity4.last_call("turn_on")
    assert data == {"brightness": 128, "rgbw_color": (128, 0, 0, 0)}
    _, data = entity5.last_call("turn_on")
    assert data == {"brightness": 128, "rgbww_color": (128, 0, 0, 0, 0)}
    _, data = entity6.last_call("turn_on")
    assert data == {"brightness": 128, "color_temp_kelvin": 6279}

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
                entity6.entity_id,
            ],
            "brightness_pct": 50,
            "rgb_color": (255, 255, 255),
        },
        blocking=True,
    )
    _, data = entity0.last_call("turn_on")
    assert data == {"brightness": 128, "hs_color": (0.0, 0.0)}
    _, data = entity1.last_call("turn_on")
    assert data == {"brightness": 128, "rgb_color": (255, 255, 255)}
    _, data = entity2.last_call("turn_on")
    assert data == {"brightness": 128, "xy_color": (0.323, 0.329)}
    _, data = entity3.last_call("turn_on")
    assert data == {"brightness": 128, "rgb_color": (255, 255, 255)}
    _, data = entity4.last_call("turn_on")
    assert data == {"brightness": 128, "rgbw_color": (0, 0, 0, 255)}
    _, data = entity5.last_call("turn_on")
    # The midpoint the white channels is warm, compensated by adding green + blue
    assert data == {"brightness": 128, "rgbww_color": (0, 76, 141, 255, 255)}
    _, data = entity6.last_call("turn_on")
    assert data == {"brightness": 128, "color_temp_kelvin": 5962}

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
                entity6.entity_id,
            ],
            "brightness_pct": 50,
            "xy_color": (0.1, 0.8),
        },
        blocking=True,
    )
    _, data = entity0.last_call("turn_on")
    assert data == {"brightness": 128, "hs_color": (125.176, 100.0)}
    _, data = entity1.last_call("turn_on")
    assert data == {"brightness": 128, "rgb_color": (0, 255, 22)}
    _, data = entity2.last_call("turn_on")
    assert data == {"brightness": 128, "xy_color": (0.1, 0.8)}
    _, data = entity3.last_call("turn_on")
    assert data == {"brightness": 128, "xy_color": (0.1, 0.8)}
    _, data = entity4.last_call("turn_on")
    assert data == {"brightness": 128, "rgbw_color": (0, 255, 22, 0)}
    _, data = entity5.last_call("turn_on")
    assert data == {"brightness": 128, "rgbww_color": (0, 255, 22, 0, 0)}
    _, data = entity6.last_call("turn_on")
    assert data == {"brightness": 128, "color_temp_kelvin": 8645}

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
                entity6.entity_id,
            ],
            "brightness_pct": 50,
            "xy_color": (0.323, 0.329),
        },
        blocking=True,
    )
    _, data = entity0.last_call("turn_on")
    assert data == {"brightness": 128, "hs_color": (0.0, 0.392)}
    _, data = entity1.last_call("turn_on")
    assert data == {"brightness": 128, "rgb_color": (255, 254, 254)}
    _, data = entity2.last_call("turn_on")
    assert data == {"brightness": 128, "xy_color": (0.323, 0.329)}
    _, data = entity3.last_call("turn_on")
    assert data == {"brightness": 128, "xy_color": (0.323, 0.329)}
    _, data = entity4.last_call("turn_on")
    assert data == {"brightness": 128, "rgbw_color": (1, 0, 0, 255)}
    _, data = entity5.last_call("turn_on")
    # The midpoint the white channels is warm, compensated by adding green + blue
    assert data == {"brightness": 128, "rgbww_color": (0, 75, 140, 255, 255)}
    _, data = entity6.last_call("turn_on")
    assert data == {"brightness": 128, "color_temp_kelvin": 5962}

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
                entity6.entity_id,
            ],
            "brightness_pct": 50,
            "rgbw_color": (128, 0, 0, 64),
        },
        blocking=True,
    )
    _, data = entity0.last_call("turn_on")
    assert data == {"brightness": 128, "hs_color": (0.0, 66.406)}
    _, data = entity1.last_call("turn_on")
    assert data == {"brightness": 128, "rgb_color": (128, 43, 43)}
    _, data = entity2.last_call("turn_on")
    assert data == {"brightness": 128, "xy_color": (0.592, 0.308)}
    _, data = entity3.last_call("turn_on")
    assert data == {"brightness": 128, "rgb_color": (128, 43, 43)}
    _, data = entity4.last_call("turn_on")
    assert data == {"brightness": 128, "rgbw_color": (128, 0, 0, 64)}
    _, data = entity5.last_call("turn_on")
    # The midpoint the white channels is warm, compensated by adding green + blue
    assert data == {"brightness": 128, "rgbww_color": (128, 0, 30, 117, 117)}
    _, data = entity6.last_call("turn_on")
    assert data == {"brightness": 128, "color_temp_kelvin": 3011}

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
                entity6.entity_id,
            ],
            "brightness_pct": 50,
            "rgbw_color": (255, 255, 255, 255),
        },
        blocking=True,
    )
    _, data = entity0.last_call("turn_on")
    assert data == {"brightness": 128, "hs_color": (0.0, 0.0)}
    _, data = entity1.last_call("turn_on")
    assert data == {"brightness": 128, "rgb_color": (255, 255, 255)}
    _, data = entity2.last_call("turn_on")
    assert data == {"brightness": 128, "xy_color": (0.323, 0.329)}
    _, data = entity3.last_call("turn_on")
    assert data == {"brightness": 128, "rgb_color": (255, 255, 255)}
    _, data = entity4.last_call("turn_on")
    assert data == {"brightness": 128, "rgbw_color": (255, 255, 255, 255)}
    _, data = entity5.last_call("turn_on")
    # The midpoint the white channels is warm, compensated by adding green + blue
    assert data == {"brightness": 128, "rgbww_color": (0, 76, 141, 255, 255)}
    _, data = entity6.last_call("turn_on")
    assert data == {"brightness": 128, "color_temp_kelvin": 5962}

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
                entity6.entity_id,
            ],
            "brightness_pct": 50,
            "rgbww_color": (128, 0, 0, 64, 32),
        },
        blocking=True,
    )
    _, data = entity0.last_call("turn_on")
    assert data == {"brightness": 128, "hs_color": (4.118, 79.688)}
    _, data = entity1.last_call("turn_on")
    assert data == {"brightness": 128, "rgb_color": (128, 33, 26)}
    _, data = entity2.last_call("turn_on")
    assert data == {"brightness": 128, "xy_color": (0.639, 0.312)}
    _, data = entity3.last_call("turn_on")
    assert data == {"brightness": 128, "rgb_color": (128, 33, 26)}
    _, data = entity4.last_call("turn_on")
    assert data == {"brightness": 128, "rgbw_color": (128, 9, 0, 33)}
    _, data = entity5.last_call("turn_on")
    assert data == {"brightness": 128, "rgbww_color": (128, 0, 0, 64, 32)}
    _, data = entity6.last_call("turn_on")
    assert data == {"brightness": 128, "color_temp_kelvin": 3845}

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
                entity6.entity_id,
            ],
            "brightness_pct": 50,
            "rgbww_color": (255, 255, 255, 255, 255),
        },
        blocking=True,
    )
    _, data = entity0.last_call("turn_on")
    assert data == {"brightness": 128, "hs_color": (27.429, 27.451)}
    _, data = entity1.last_call("turn_on")
    assert data == {"brightness": 128, "rgb_color": (255, 217, 185)}
    _, data = entity2.last_call("turn_on")
    assert data == {"brightness": 128, "xy_color": (0.396, 0.359)}
    _, data = entity3.last_call("turn_on")
    assert data == {"brightness": 128, "rgb_color": (255, 217, 185)}
    _, data = entity4.last_call("turn_on")
    # The midpoint the white channels is warm, compensated by decreasing green + blue
    assert data == {"brightness": 128, "rgbw_color": (96, 44, 0, 255)}
    _, data = entity5.last_call("turn_on")
    assert data == {"brightness": 128, "rgbww_color": (255, 255, 255, 255, 255)}
    _, data = entity6.last_call("turn_on")
    assert data == {"brightness": 128, "color_temp_kelvin": 3451}