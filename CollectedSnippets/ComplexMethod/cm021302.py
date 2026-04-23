async def test_restore_state(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ensure states are restored on startup."""
    config = {
        "rflink": {"port": "/dev/ttyABC0"},
        DOMAIN: {
            "platform": "rflink",
            "devices": {
                "RTS_12345678_0": {"name": "c1"},
                "test_restore_2": {"name": "c2"},
                "test_restore_3": {"name": "c3"},
                "test_restore_4": {"name": "c4"},
            },
        },
    }

    mock_restore_cache(
        hass,
        (
            State(f"{DOMAIN}.c1", CoverState.OPEN),
            State(f"{DOMAIN}.c2", CoverState.CLOSED),
        ),
    )

    hass.set_state(CoreState.starting)

    # setup mocking rflink module
    _, _, _, _ = await mock_rflink(hass, config, DOMAIN, monkeypatch)

    state = hass.states.get(f"{DOMAIN}.c1")
    assert state
    assert state.state == CoverState.OPEN

    state = hass.states.get(f"{DOMAIN}.c2")
    assert state
    assert state.state == CoverState.CLOSED

    state = hass.states.get(f"{DOMAIN}.c3")
    assert state
    assert state.state == CoverState.CLOSED

    # not cached cover must default values
    state = hass.states.get(f"{DOMAIN}.c4")
    assert state
    assert state.state == CoverState.CLOSED
    assert state.attributes["assumed_state"]