async def test_mode(hass: HomeAssistant) -> None:
    """Test mode settings."""
    assert await async_setup_component(
        hass,
        DOMAIN,
        {
            DOMAIN: {
                "test_default_text": {"initial": "test", "min": 3, "max": 10},
                "test_explicit_text": {
                    "initial": "test",
                    "min": 3,
                    "max": 10,
                    "mode": "text",
                },
                "test_explicit_password": {
                    "initial": "test",
                    "min": 3,
                    "max": 10,
                    "mode": "password",
                },
            }
        },
    )

    state = hass.states.get("input_text.test_default_text")
    assert state
    assert state.attributes["mode"] == "text"

    state = hass.states.get("input_text.test_explicit_text")
    assert state
    assert state.attributes["mode"] == "text"

    state = hass.states.get("input_text.test_explicit_password")
    assert state
    assert state.attributes["mode"] == "password"