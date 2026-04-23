async def test_entity_cast_status(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test handling of cast status."""
    entity_id = "media_player.speaker"

    info = get_fake_chromecast_info()

    chromecast, _ = await async_setup_media_player_cast(hass, info)
    chromecast.cast_type = pychromecast.const.CAST_TYPE_CHROMECAST
    cast_status_cb, conn_status_cb, _ = get_status_callbacks(chromecast)

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

    # No media status, pause, play, stop not supported
    assert state.attributes.get("supported_features") == (
        MediaPlayerEntityFeature.PLAY_MEDIA
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.VOLUME_SET
    )

    cast_status = MagicMock()
    cast_status.volume_level = 0.5
    cast_status.volume_muted = False
    cast_status_cb(cast_status)
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    # Volume hidden if no app is active
    assert state.attributes.get("volume_level") is None
    assert not state.attributes.get("is_volume_muted")

    chromecast.app_id = "1234"
    cast_status = MagicMock()
    cast_status.volume_level = 0.5
    cast_status.volume_muted = False
    cast_status_cb(cast_status)
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.attributes.get("volume_level") == 0.5
    assert not state.attributes.get("is_volume_muted")

    cast_status = MagicMock()
    cast_status.volume_level = 0.2
    cast_status.volume_muted = True
    cast_status_cb(cast_status)
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.attributes.get("volume_level") == 0.2
    assert state.attributes.get("is_volume_muted")

    # Disable support for volume control
    cast_status = MagicMock()
    cast_status.volume_control_type = "fixed"
    cast_status_cb(cast_status)
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.attributes.get("supported_features") == (
        MediaPlayerEntityFeature.PLAY_MEDIA
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.TURN_ON
    )