async def test_set_level_command(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test 'set_level=XX' events."""
    config = {
        "rflink": {"port": "/dev/ttyABC0"},
        DOMAIN: {
            "platform": "rflink",
            "devices": {
                "newkaku_12345678_0": {"name": "l1"},
                "test_no_dimmable": {"name": "l2"},
                "test_dimmable": {"name": "l3", "type": "dimmable"},
                "test_hybrid": {"name": "l4", "type": "hybrid"},
            },
        },
    }

    # setup mocking rflink module
    event_callback, _, _, _ = await mock_rflink(hass, config, DOMAIN, monkeypatch)

    # test sending command to a newkaku device
    event_callback({"id": "newkaku_12345678_0", "command": "set_level=10"})
    await hass.async_block_till_done()
    # should affect state
    state = hass.states.get(f"{DOMAIN}.l1")
    assert state
    assert state.state == STATE_ON
    assert state.attributes[ATTR_BRIGHTNESS] == 170
    # turn off
    event_callback({"id": "newkaku_12345678_0", "command": "off"})
    await hass.async_block_till_done()
    state = hass.states.get(f"{DOMAIN}.l1")
    assert state
    assert state.state == STATE_OFF
    # off light shouldn't have brightness
    assert not state.attributes.get(ATTR_BRIGHTNESS)
    # turn on
    event_callback({"id": "newkaku_12345678_0", "command": "on"})
    await hass.async_block_till_done()
    state = hass.states.get(f"{DOMAIN}.l1")
    assert state
    assert state.state == STATE_ON
    assert state.attributes[ATTR_BRIGHTNESS] == 170

    # test sending command to a no dimmable device
    event_callback({"id": "test_no_dimmable", "command": "set_level=10"})
    await hass.async_block_till_done()
    # should NOT affect state
    state = hass.states.get(f"{DOMAIN}.l2")
    assert state
    assert state.state == STATE_OFF
    assert not state.attributes.get(ATTR_BRIGHTNESS)

    # test sending command to a dimmable device
    event_callback({"id": "test_dimmable", "command": "set_level=5"})
    await hass.async_block_till_done()
    # should affect state
    state = hass.states.get(f"{DOMAIN}.l3")
    assert state
    assert state.state == STATE_ON
    assert state.attributes[ATTR_BRIGHTNESS] == 85

    # test sending command to a hybrid device
    event_callback({"id": "test_hybrid", "command": "set_level=15"})
    await hass.async_block_till_done()
    # should affect state
    state = hass.states.get(f"{DOMAIN}.l4")
    assert state
    assert state.state == STATE_ON
    assert state.attributes[ATTR_BRIGHTNESS] == 255

    event_callback({"id": "test_hybrid", "command": "off"})
    await hass.async_block_till_done()
    # should affect state
    state = hass.states.get(f"{DOMAIN}.l4")
    assert state
    assert state.state == STATE_OFF
    # off light shouldn't have brightness
    assert not state.attributes.get(ATTR_BRIGHTNESS)

    event_callback({"id": "test_hybrid", "command": "set_level=0"})
    await hass.async_block_till_done()
    # should affect state
    state = hass.states.get(f"{DOMAIN}.l4")
    assert state
    assert state.state == STATE_ON
    assert state.attributes[ATTR_BRIGHTNESS] == 0