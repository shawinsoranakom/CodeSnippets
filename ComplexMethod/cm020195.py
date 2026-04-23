async def test_updates_from_connection_event(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    controller: MockHeos,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Tests player updates from connection event after connection failure."""
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    player = controller.players[1]

    # Connected
    player.available = True
    await controller.dispatcher.wait_send(
        SignalType.HEOS_EVENT, SignalHeosEvent.CONNECTED
    )
    await hass.async_block_till_done()
    state = hass.states.get("media_player.test_player")
    assert state is not None
    assert state.state == STATE_IDLE

    # Disconnected
    controller.load_players.reset_mock()
    player.available = False
    await controller.dispatcher.wait_send(
        SignalType.HEOS_EVENT, SignalHeosEvent.DISCONNECTED
    )
    await hass.async_block_till_done()
    state = hass.states.get("media_player.test_player")
    assert state is not None
    assert state.state == STATE_UNAVAILABLE

    # Reconnect and state updates
    player.available = True
    await controller.dispatcher.wait_send(
        SignalType.HEOS_EVENT, SignalHeosEvent.CONNECTED
    )
    await hass.async_block_till_done()
    state = hass.states.get("media_player.test_player")
    assert state is not None
    assert state.state == STATE_IDLE