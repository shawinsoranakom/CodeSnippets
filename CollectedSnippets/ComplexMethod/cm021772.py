async def test_group_media_states(
    hass: HomeAssistant, entity_registry: er.EntityRegistry, mz_mock
) -> None:
    """Test media states are read from group if entity has no state."""
    entity_id = "media_player.speaker"

    info = get_fake_chromecast_info()

    chromecast, _ = await async_setup_media_player_cast(hass, info)
    _, conn_status_cb, media_status_cb, group_media_status_cb = get_status_callbacks(
        chromecast, mz_mock
    )

    connection_status = MagicMock()
    connection_status.status = "CONNECTED"
    conn_status_cb(connection_status)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.name == "Speaker"
    assert state.state == "off"
    assert entity_id == entity_registry.async_get_entity_id(
        "media_player", "cast", str(info.uuid)
    )

    group_media_status = MagicMock(images=None)
    player_media_status = MagicMock(images=None)

    # Player has no state, group is buffering -> Should report 'buffering'
    group_media_status.player_state = "BUFFERING"
    group_media_status_cb(str(FakeGroupUUID), group_media_status)
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == "buffering"

    # Player has no state, group is playing -> Should report 'playing'
    group_media_status.player_state = "PLAYING"
    group_media_status_cb(str(FakeGroupUUID), group_media_status)
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == "playing"

    # Player is paused, group is playing -> Should report 'paused'
    player_media_status.player_state = None
    player_media_status.player_is_paused = True
    media_status_cb(player_media_status)
    await hass.async_block_till_done()
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == "paused"

    # Player is in unknown state, group is playing -> Should report 'playing'
    player_media_status.player_state = "UNKNOWN"
    media_status_cb(player_media_status)
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == "playing"