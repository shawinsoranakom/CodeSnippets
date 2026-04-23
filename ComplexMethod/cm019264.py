async def test_service_calls(hass: HomeAssistant, mock_media_seek: Mock) -> None:
    """Test service calls."""
    await async_setup_component(
        hass,
        MEDIA_DOMAIN,
        {
            MEDIA_DOMAIN: [
                {"platform": "demo"},
                {
                    "platform": DOMAIN,
                    "entities": [
                        "media_player.bedroom",
                        "media_player.kitchen",
                        "media_player.living_room",
                    ],
                },
            ]
        },
    )
    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()

    assert hass.states.get("media_player.media_group").state == STATE_PLAYING
    await hass.services.async_call(
        MEDIA_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "media_player.media_group"},
        blocking=True,
    )

    await hass.async_block_till_done()
    assert hass.states.get("media_player.bedroom").state == STATE_OFF
    assert hass.states.get("media_player.kitchen").state == STATE_OFF
    assert hass.states.get("media_player.living_room").state == STATE_OFF

    await hass.services.async_call(
        MEDIA_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "media_player.media_group"},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert hass.states.get("media_player.bedroom").state == STATE_PLAYING
    assert hass.states.get("media_player.kitchen").state == STATE_PLAYING
    assert hass.states.get("media_player.living_room").state == STATE_PLAYING

    await hass.services.async_call(
        MEDIA_DOMAIN,
        SERVICE_MEDIA_PAUSE,
        {ATTR_ENTITY_ID: "media_player.media_group"},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert hass.states.get("media_player.bedroom").state == STATE_PAUSED
    assert hass.states.get("media_player.kitchen").state == STATE_PAUSED
    assert hass.states.get("media_player.living_room").state == STATE_PAUSED

    await hass.services.async_call(
        MEDIA_DOMAIN,
        SERVICE_MEDIA_PLAY,
        {ATTR_ENTITY_ID: "media_player.media_group"},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert hass.states.get("media_player.bedroom").state == STATE_PLAYING
    assert hass.states.get("media_player.kitchen").state == STATE_PLAYING
    assert hass.states.get("media_player.living_room").state == STATE_PLAYING

    # ATTR_MEDIA_TRACK is not supported by bedroom and living_room players
    assert hass.states.get("media_player.kitchen").attributes[ATTR_MEDIA_TRACK] == 1
    await hass.services.async_call(
        MEDIA_DOMAIN,
        SERVICE_MEDIA_NEXT_TRACK,
        {ATTR_ENTITY_ID: "media_player.media_group"},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert hass.states.get("media_player.kitchen").attributes[ATTR_MEDIA_TRACK] == 2

    await hass.services.async_call(
        MEDIA_DOMAIN,
        SERVICE_MEDIA_PREVIOUS_TRACK,
        {ATTR_ENTITY_ID: "media_player.media_group"},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert hass.states.get("media_player.kitchen").attributes[ATTR_MEDIA_TRACK] == 1

    await hass.services.async_call(
        MEDIA_DOMAIN,
        SERVICE_PLAY_MEDIA,
        {
            ATTR_ENTITY_ID: "media_player.media_group",
            ATTR_MEDIA_CONTENT_TYPE: "some_type",
            ATTR_MEDIA_CONTENT_ID: "some_id",
        },
    )
    await hass.async_block_till_done()
    assert (
        hass.states.get("media_player.bedroom").attributes[ATTR_MEDIA_CONTENT_ID]
        == "some_id"
    )
    # media_player.kitchen is skipped because it always returns "bounzz-1"
    assert (
        hass.states.get("media_player.living_room").attributes[ATTR_MEDIA_CONTENT_ID]
        == "some_id"
    )

    state = hass.states.get("media_player.media_group")
    assert state.attributes[ATTR_SUPPORTED_FEATURES] & MediaPlayerEntityFeature.SEEK
    assert not mock_media_seek.called

    await hass.services.async_call(
        MEDIA_DOMAIN,
        SERVICE_MEDIA_SEEK,
        {
            ATTR_ENTITY_ID: "media_player.media_group",
            ATTR_MEDIA_SEEK_POSITION: 100,
        },
    )
    await hass.async_block_till_done()
    assert mock_media_seek.called

    assert (
        hass.states.get("media_player.bedroom").attributes[ATTR_MEDIA_VOLUME_LEVEL] == 1
    )
    assert (
        hass.states.get("media_player.kitchen").attributes[ATTR_MEDIA_VOLUME_LEVEL] == 1
    )
    assert (
        hass.states.get("media_player.living_room").attributes[ATTR_MEDIA_VOLUME_LEVEL]
        == 1
    )
    await hass.services.async_call(
        MEDIA_DOMAIN,
        SERVICE_VOLUME_SET,
        {
            ATTR_ENTITY_ID: "media_player.media_group",
            ATTR_MEDIA_VOLUME_LEVEL: 0.5,
        },
        blocking=True,
    )
    await hass.async_block_till_done()
    assert (
        hass.states.get("media_player.bedroom").attributes[ATTR_MEDIA_VOLUME_LEVEL]
        == 0.5
    )
    assert (
        hass.states.get("media_player.kitchen").attributes[ATTR_MEDIA_VOLUME_LEVEL]
        == 0.5
    )
    assert (
        hass.states.get("media_player.living_room").attributes[ATTR_MEDIA_VOLUME_LEVEL]
        == 0.5
    )

    await hass.services.async_call(
        MEDIA_DOMAIN,
        SERVICE_VOLUME_UP,
        {ATTR_ENTITY_ID: "media_player.media_group"},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert (
        hass.states.get("media_player.bedroom").attributes[ATTR_MEDIA_VOLUME_LEVEL]
        == 0.6
    )
    assert (
        hass.states.get("media_player.kitchen").attributes[ATTR_MEDIA_VOLUME_LEVEL]
        == 0.6
    )
    assert (
        hass.states.get("media_player.living_room").attributes[ATTR_MEDIA_VOLUME_LEVEL]
        == 0.6
    )

    await hass.services.async_call(
        MEDIA_DOMAIN,
        SERVICE_VOLUME_DOWN,
        {ATTR_ENTITY_ID: "media_player.media_group"},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert (
        hass.states.get("media_player.bedroom").attributes[ATTR_MEDIA_VOLUME_LEVEL]
        == 0.5
    )
    assert (
        hass.states.get("media_player.kitchen").attributes[ATTR_MEDIA_VOLUME_LEVEL]
        == 0.5
    )
    assert (
        hass.states.get("media_player.living_room").attributes[ATTR_MEDIA_VOLUME_LEVEL]
        == 0.5
    )

    assert (
        hass.states.get("media_player.bedroom").attributes[ATTR_MEDIA_VOLUME_MUTED]
        is False
    )
    assert (
        hass.states.get("media_player.kitchen").attributes[ATTR_MEDIA_VOLUME_MUTED]
        is False
    )
    assert (
        hass.states.get("media_player.living_room").attributes[ATTR_MEDIA_VOLUME_MUTED]
        is False
    )
    await hass.services.async_call(
        MEDIA_DOMAIN,
        SERVICE_VOLUME_MUTE,
        {ATTR_ENTITY_ID: "media_player.media_group", ATTR_MEDIA_VOLUME_MUTED: True},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert (
        hass.states.get("media_player.bedroom").attributes[ATTR_MEDIA_VOLUME_MUTED]
        is True
    )
    assert (
        hass.states.get("media_player.kitchen").attributes[ATTR_MEDIA_VOLUME_MUTED]
        is True
    )
    assert (
        hass.states.get("media_player.living_room").attributes[ATTR_MEDIA_VOLUME_MUTED]
        is True
    )

    assert (
        hass.states.get("media_player.bedroom").attributes[ATTR_MEDIA_SHUFFLE] is False
    )
    assert (
        hass.states.get("media_player.kitchen").attributes[ATTR_MEDIA_SHUFFLE] is False
    )
    assert (
        hass.states.get("media_player.living_room").attributes[ATTR_MEDIA_SHUFFLE]
        is False
    )
    await hass.services.async_call(
        MEDIA_DOMAIN,
        SERVICE_SHUFFLE_SET,
        {ATTR_ENTITY_ID: "media_player.media_group", ATTR_MEDIA_SHUFFLE: True},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert (
        hass.states.get("media_player.bedroom").attributes[ATTR_MEDIA_SHUFFLE] is True
    )
    assert (
        hass.states.get("media_player.kitchen").attributes[ATTR_MEDIA_SHUFFLE] is True
    )
    assert (
        hass.states.get("media_player.living_room").attributes[ATTR_MEDIA_SHUFFLE]
        is True
    )

    assert hass.states.get("media_player.bedroom").state == STATE_PLAYING
    assert hass.states.get("media_player.kitchen").state == STATE_PLAYING
    assert hass.states.get("media_player.living_room").state == STATE_PLAYING
    await hass.services.async_call(
        MEDIA_DOMAIN,
        SERVICE_CLEAR_PLAYLIST,
        {ATTR_ENTITY_ID: "media_player.media_group"},
        blocking=True,
    )
    await hass.async_block_till_done()
    # SERVICE_CLEAR_PLAYLIST is not supported by bedroom and living_room players
    assert hass.states.get("media_player.kitchen").state == STATE_OFF

    await hass.services.async_call(
        MEDIA_DOMAIN,
        SERVICE_MEDIA_PLAY,
        {ATTR_ENTITY_ID: "media_player.kitchen"},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert hass.states.get("media_player.bedroom").state == STATE_PLAYING
    assert hass.states.get("media_player.kitchen").state == STATE_PLAYING
    assert hass.states.get("media_player.living_room").state == STATE_PLAYING
    await hass.services.async_call(
        MEDIA_DOMAIN,
        SERVICE_MEDIA_STOP,
        {ATTR_ENTITY_ID: "media_player.media_group"},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert hass.states.get("media_player.bedroom").state == STATE_OFF
    assert hass.states.get("media_player.kitchen").state == STATE_OFF
    assert hass.states.get("media_player.living_room").state == STATE_OFF