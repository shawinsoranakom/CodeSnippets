async def test_restore_state(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ensure states are restored on startup."""
    config = {
        "rflink": {"port": "/dev/ttyABC0"},
        DOMAIN: {
            "platform": "rflink",
            "devices": {
                "NewKaku_12345678_0": {"name": "l1", "type": "hybrid"},
                "test_restore_2": {"name": "l2"},
                "test_restore_3": {"name": "l3"},
                "test_restore_4": {"name": "l4", "type": "dimmable"},
                "test_restore_5": {"name": "l5", "type": "dimmable"},
            },
        },
    }

    mock_restore_cache(
        hass,
        (
            State(f"{DOMAIN}.l1", STATE_ON, {ATTR_BRIGHTNESS: "123"}),
            State(f"{DOMAIN}.l2", STATE_ON, {ATTR_BRIGHTNESS: "321"}),
            State(f"{DOMAIN}.l3", STATE_OFF),
            State(f"{DOMAIN}.l5", STATE_ON, {ATTR_BRIGHTNESS: "222"}),
        ),
    )

    hass.set_state(CoreState.starting)

    # setup mocking rflink module
    _, _, _, _ = await mock_rflink(hass, config, DOMAIN, monkeypatch)

    # hybrid light must restore brightness
    state = hass.states.get(f"{DOMAIN}.l1")
    assert state
    assert state.state == STATE_ON
    assert state.attributes[ATTR_BRIGHTNESS] == 123

    # normal light do NOT must restore brightness
    state = hass.states.get(f"{DOMAIN}.l2")
    assert state
    assert state.state == STATE_ON
    assert not state.attributes.get(ATTR_BRIGHTNESS)

    # OFF state also restores (or not)
    state = hass.states.get(f"{DOMAIN}.l3")
    assert state
    assert state.state == STATE_OFF

    # not cached light must default values
    state = hass.states.get(f"{DOMAIN}.l4")
    assert state
    assert state.state == STATE_OFF
    # off light shouldn't have brightness
    assert not state.attributes.get(ATTR_BRIGHTNESS)
    assert state.attributes["assumed_state"]

    # test coverage for dimmable light
    state = hass.states.get(f"{DOMAIN}.l5")
    assert state
    assert state.state == STATE_ON
    assert state.attributes[ATTR_BRIGHTNESS] == 222