async def test_mode(hass: HomeAssistant) -> None:
    """Test mode settings."""
    assert await async_setup_component(
        hass,
        DOMAIN,
        {
            DOMAIN: {
                "test_default_slider": {"min": 0, "max": 100},
                "test_explicit_box": {"min": 0, "max": 100, "mode": "box"},
                "test_explicit_slider": {"min": 0, "max": 100, "mode": "slider"},
            }
        },
    )

    state = hass.states.get("input_number.test_default_slider")
    assert state
    assert state.attributes["mode"] == "slider"

    state = hass.states.get("input_number.test_explicit_box")
    assert state
    assert state.attributes["mode"] == "box"

    state = hass.states.get("input_number.test_explicit_slider")
    assert state
    assert state.attributes["mode"] == "slider"