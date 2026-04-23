async def test_light_service_call_white_mode(hass: HomeAssistant) -> None:
    """Test color_mode white in service calls."""
    entity0 = MockLight("Test_white", STATE_ON)
    entity0.supported_color_modes = {light.ColorMode.HS, light.ColorMode.WHITE}
    entity0.color_mode = light.ColorMode.HS
    setup_test_component_platform(hass, light.DOMAIN, [entity0])

    assert await async_setup_component(hass, "light", {"light": {"platform": "test"}})
    await hass.async_block_till_done()

    state = hass.states.get(entity0.entity_id)
    assert state.attributes["supported_color_modes"] == [
        light.ColorMode.HS,
        light.ColorMode.WHITE,
    ]

    await hass.services.async_call(
        "light",
        "turn_on",
        {
            "entity_id": [entity0.entity_id],
            "brightness_pct": 100,
            "hs_color": (240, 100),
        },
        blocking=True,
    )
    _, data = entity0.last_call("turn_on")
    assert data == {"brightness": 255, "hs_color": (240.0, 100.0)}

    entity0.calls = []
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": [entity0.entity_id], "white": 50},
        blocking=True,
    )
    _, data = entity0.last_call("turn_on")
    assert data == {"white": 50}

    entity0.calls = []
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": [entity0.entity_id], "white": 0},
        blocking=True,
    )
    _, data = entity0.last_call("turn_off")
    assert data == {}

    entity0.calls = []
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": [entity0.entity_id], "brightness_pct": 100, "white": 50},
        blocking=True,
    )
    _, data = entity0.last_call("turn_on")
    assert data == {"white": 255}

    entity0.calls = []
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": [entity0.entity_id], "brightness": 100, "white": 0},
        blocking=True,
    )
    _, data = entity0.last_call("turn_on")
    assert data == {"white": 100}

    entity0.calls = []
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": [entity0.entity_id], "brightness_pct": 0, "white": 50},
        blocking=True,
    )
    _, data = entity0.last_call("turn_off")
    assert data == {}

    entity0.calls = []
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": [entity0.entity_id], "white": True},
        blocking=True,
    )
    _, data = entity0.last_call("turn_on")
    assert data == {"white": 100}

    entity0.calls = []
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": [entity0.entity_id], "brightness_pct": 50, "white": True},
        blocking=True,
    )
    _, data = entity0.last_call("turn_on")
    assert data == {"white": 128}