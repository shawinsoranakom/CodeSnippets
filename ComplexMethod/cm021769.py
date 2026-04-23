async def test_entity_media_states(
    hass: HomeAssistant, entity_registry: er.EntityRegistry, app_id, state_no_media
) -> None:
    """Test various entity media states."""
    entity_id = "media_player.speaker"

    info = get_fake_chromecast_info()

    chromecast, _ = await async_setup_media_player_cast(hass, info)
    cast_status_cb, conn_status_cb, media_status_cb = get_status_callbacks(chromecast)

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

    # App id updated, but no media status
    chromecast.app_id = app_id
    cast_status = MagicMock()
    cast_status_cb(cast_status)
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == state_no_media

    # Got media status
    media_status = MagicMock(images=None)
    media_status.player_state = "BUFFERING"
    media_status_cb(media_status)
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == "buffering"

    media_status.player_state = "PLAYING"
    media_status_cb(media_status)
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == "playing"

    media_status.player_state = None
    media_status.player_is_paused = True
    media_status_cb(media_status)
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == "paused"

    media_status.player_is_paused = False
    media_status.player_is_idle = True
    media_status_cb(media_status)
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == "idle"

    # No media status, app is still running
    media_status_cb(None)
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == state_no_media

    # App no longer running
    chromecast.app_id = pychromecast.IDLE_APP_ID
    cast_status = MagicMock()
    cast_status_cb(cast_status)
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == "off"

    # No cast status
    chromecast.app_id = None
    cast_status_cb(None)
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == "unknown"