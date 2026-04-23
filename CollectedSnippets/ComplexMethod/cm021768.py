async def test_entity_media_content_type(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    cast_type,
    default_content_type,
) -> None:
    """Test various content types."""
    entity_id = "media_player.speaker"

    info = get_fake_chromecast_info()

    chromecast, _ = await async_setup_media_player_cast(hass, info)
    chromecast.cast_type = cast_type
    _, conn_status_cb, media_status_cb = get_status_callbacks(chromecast)

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

    media_status = MagicMock(images=None)
    media_status.media_is_movie = False
    media_status.media_is_musictrack = False
    media_status.media_is_tvshow = False
    media_status_cb(media_status)
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.attributes.get("media_content_type") == default_content_type

    media_status.media_is_tvshow = True
    media_status_cb(media_status)
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.attributes.get("media_content_type") == "tvshow"

    media_status.media_is_tvshow = False
    media_status.media_is_musictrack = True
    media_status_cb(media_status)
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.attributes.get("media_content_type") == "music"

    media_status.media_is_musictrack = True
    media_status.media_is_movie = True
    media_status_cb(media_status)
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.attributes.get("media_content_type") == "movie"