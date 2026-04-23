async def test_light_brightness_pct_conversion(
    hass: HomeAssistant,
    mock_light_entities: list[MockLight],
) -> None:
    """Test that light brightness percent conversion."""
    setup_test_component_platform(hass, light.DOMAIN, mock_light_entities)

    entity = mock_light_entities[0]
    entity.supported_color_modes = {light.ColorMode.BRIGHTNESS}
    entity.color_mode = light.ColorMode.BRIGHTNESS
    entity.brightness = 100
    assert await async_setup_component(hass, "light", {"light": {"platform": "test"}})
    await hass.async_block_till_done()

    state = hass.states.get(entity.entity_id)
    assert state is not None
    assert state.attributes["brightness"] == 100

    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": entity.entity_id, "brightness_pct": 1},
        blocking=True,
    )

    _, data = entity.last_call("turn_on")
    assert data["brightness"] == 3

    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": entity.entity_id, "brightness_pct": 2},
        blocking=True,
    )

    _, data = entity.last_call("turn_on")
    assert data["brightness"] == 5

    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": entity.entity_id, "brightness_pct": 50},
        blocking=True,
    )

    _, data = entity.last_call("turn_on")
    assert data["brightness"] == 128

    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": entity.entity_id, "brightness_pct": 99},
        blocking=True,
    )

    _, data = entity.last_call("turn_on")
    assert data["brightness"] == 252

    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": entity.entity_id, "brightness_pct": 100},
        blocking=True,
    )

    _, data = entity.last_call("turn_on")
    assert data["brightness"] == 255