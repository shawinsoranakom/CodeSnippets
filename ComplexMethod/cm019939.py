async def test_light_service_call_color_temp_emulation(hass: HomeAssistant) -> None:
    """Test color conversion in service calls."""
    entities = [
        MockLight("Test_hs_ct", STATE_ON),
        MockLight("Test_hs", STATE_ON),
        MockLight("Test_hs_white", STATE_ON),
    ]
    setup_test_component_platform(hass, light.DOMAIN, entities)

    entity0 = entities[0]
    entity0.supported_color_modes = {light.ColorMode.COLOR_TEMP, light.ColorMode.HS}
    entity0.color_mode = light.ColorMode.COLOR_TEMP

    entity1 = entities[1]
    entity1.supported_color_modes = {light.ColorMode.HS}
    entity1.color_mode = light.ColorMode.HS

    entity2 = entities[2]
    entity2.supported_color_modes = {light.ColorMode.HS, light.ColorMode.WHITE}
    entity2.color_mode = light.ColorMode.HS

    assert await async_setup_component(hass, "light", {"light": {"platform": "test"}})
    await hass.async_block_till_done()

    state = hass.states.get(entity0.entity_id)
    assert state.attributes["supported_color_modes"] == [
        light.ColorMode.COLOR_TEMP,
        light.ColorMode.HS,
    ]

    state = hass.states.get(entity1.entity_id)
    assert state.attributes["supported_color_modes"] == [light.ColorMode.HS]

    state = hass.states.get(entity2.entity_id)
    assert state.attributes["supported_color_modes"] == [
        light.ColorMode.HS,
        light.ColorMode.WHITE,
    ]

    await hass.services.async_call(
        "light",
        "turn_on",
        {
            "entity_id": [
                entity0.entity_id,
                entity1.entity_id,
                entity2.entity_id,
            ],
            "brightness_pct": 100,
            "color_temp_kelvin": 5000,
        },
        blocking=True,
    )
    _, data = entity0.last_call("turn_on")
    assert data == {"brightness": 255, "color_temp_kelvin": 5000}
    _, data = entity1.last_call("turn_on")
    assert data == {"brightness": 255, "hs_color": (27.001, 19.243)}
    _, data = entity2.last_call("turn_on")
    assert data == {"brightness": 255, "hs_color": (27.001, 19.243)}