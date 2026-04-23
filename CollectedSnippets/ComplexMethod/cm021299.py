async def test_restore_state(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ensure states are restored on startup."""
    config = {
        "rflink": {"port": "/dev/ttyABC0"},
        DOMAIN: {
            "platform": "rflink",
            "devices": {
                "test": {"name": "s1", "aliases": ["test_alias_0_0"]},
                "switch_test": {"name": "s2"},
                "switch_s3": {"name": "s3"},
            },
        },
    }

    mock_restore_cache(
        hass, (State(f"{DOMAIN}.s1", STATE_ON), State(f"{DOMAIN}.s2", STATE_OFF))
    )

    hass.set_state(CoreState.starting)

    # setup mocking rflink module
    _, _, _, _ = await mock_rflink(hass, config, DOMAIN, monkeypatch)

    state = hass.states.get(f"{DOMAIN}.s1")
    assert state
    assert state.state == STATE_ON

    state = hass.states.get(f"{DOMAIN}.s2")
    assert state
    assert state.state == STATE_OFF

    # not cached switch must default values
    state = hass.states.get(f"{DOMAIN}.s3")
    assert state
    assert state.state == STATE_OFF
    assert state.attributes["assumed_state"]