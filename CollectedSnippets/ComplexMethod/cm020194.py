async def test_updates_from_signals(
    hass: HomeAssistant, config_entry: MockConfigEntry, controller: MockHeos
) -> None:
    """Tests dispatched signals update player."""
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    player = controller.players[1]

    # Test player does not update for other players
    player.state = PlayState.PLAY
    await controller.dispatcher.wait_send(
        SignalType.PLAYER_EVENT, 2, const.EVENT_PLAYER_STATE_CHANGED
    )
    await hass.async_block_till_done()
    state = hass.states.get("media_player.test_player")
    assert state is not None
    assert state.state == STATE_IDLE

    # Test player_update standard events
    player.state = PlayState.PLAY
    await controller.dispatcher.wait_send(
        SignalType.PLAYER_EVENT, player.player_id, const.EVENT_PLAYER_STATE_CHANGED
    )
    await hass.async_block_till_done()

    state = hass.states.get("media_player.test_player")
    assert state is not None
    assert state.state == STATE_PLAYING

    # Test player_update progress events
    player.now_playing_media.duration = 360000
    player.now_playing_media.current_position = 1000
    await controller.dispatcher.wait_send(
        SignalType.PLAYER_EVENT,
        player.player_id,
        const.EVENT_PLAYER_NOW_PLAYING_PROGRESS,
    )
    await hass.async_block_till_done()
    state = hass.states.get("media_player.test_player")
    assert state is not None
    assert state.attributes[ATTR_MEDIA_POSITION_UPDATED_AT] is not None
    assert state.attributes[ATTR_MEDIA_DURATION] == 360
    assert state.attributes[ATTR_MEDIA_POSITION] == 1