async def test_light_brightness_step(hass: HomeAssistant) -> None:
    """Test that light context works."""
    entities = [
        MockLight("Test_0", STATE_ON),
        MockLight("Test_1", STATE_ON),
    ]

    setup_test_component_platform(hass, light.DOMAIN, entities)

    entity0 = entities[0]
    entity0.supported_color_modes = {light.ColorMode.BRIGHTNESS}
    entity0.color_mode = light.ColorMode.BRIGHTNESS
    entity0.brightness = 100
    entity1 = entities[1]
    entity1.supported_color_modes = {light.ColorMode.BRIGHTNESS}
    entity1.color_mode = light.ColorMode.BRIGHTNESS
    entity1.brightness = 50
    assert await async_setup_component(hass, "light", {"light": {"platform": "test"}})
    await hass.async_block_till_done()

    state = hass.states.get(entity0.entity_id)
    assert state is not None
    assert state.attributes["brightness"] == 100
    state = hass.states.get(entity1.entity_id)
    assert state is not None
    assert state.attributes["brightness"] == 50

    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": [entity0.entity_id, entity1.entity_id], "brightness_step": -10},
        blocking=True,
    )

    _, data = entity0.last_call("turn_on")
    assert data["brightness"] == 90  # 100 - 10
    _, data = entity1.last_call("turn_on")
    assert data["brightness"] == 40  # 50 - 10

    await hass.services.async_call(
        "light",
        "turn_on",
        {
            "entity_id": entity0.entity_id,
            "brightness_step": -126,
        },
        blocking=True,
    )

    assert entity0.state == "off"