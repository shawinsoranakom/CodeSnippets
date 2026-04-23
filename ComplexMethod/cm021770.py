async def test_entity_media_states_lovelace_app(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test various entity media states when the lovelace app is active."""
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

    chromecast.app_id = CAST_APP_ID_HOMEASSISTANT_LOVELACE
    cast_status = MagicMock()
    cast_status_cb(cast_status)
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == "playing"
    assert state.attributes.get("supported_features") == (
        MediaPlayerEntityFeature.PLAY_MEDIA
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.VOLUME_SET
    )

    media_status = MagicMock(images=None)
    media_status.player_is_playing = True
    media_status_cb(media_status)
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == "playing"

    media_status.player_is_playing = False
    media_status.player_is_paused = True
    media_status_cb(media_status)
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == "playing"

    media_status.player_is_paused = False
    media_status.player_is_idle = True
    media_status_cb(media_status)
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == "playing"

    chromecast.app_id = pychromecast.IDLE_APP_ID
    media_status.player_is_idle = False
    media_status_cb(media_status)
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == "off"

    chromecast.app_id = None
    cast_status_cb(None)
    media_status_cb(media_status)
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == "unknown"