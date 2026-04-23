async def test_media_player_mute(hass: HomeAssistant) -> None:
    """Test volume trait support for muting."""
    assert trait.VolumeTrait.supported(
        media_player.DOMAIN,
        MediaPlayerEntityFeature.VOLUME_STEP | MediaPlayerEntityFeature.VOLUME_MUTE,
        None,
        None,
    )
    trt = trait.VolumeTrait(
        hass,
        State(
            "media_player.bla",
            media_player.STATE_PLAYING,
            {
                ATTR_SUPPORTED_FEATURES: (
                    MediaPlayerEntityFeature.VOLUME_STEP
                    | MediaPlayerEntityFeature.VOLUME_MUTE
                ),
                media_player.ATTR_MEDIA_VOLUME_MUTED: False,
            },
        ),
        BASIC_CONFIG,
    )

    assert trt.sync_attributes() == {
        "volumeMaxLevel": 100,
        "levelStepSize": 10,
        "volumeCanMuteAndUnmute": True,
        "commandOnlyVolume": False,
    }
    assert trt.query_attributes() == {"isMuted": False}

    mute_calls = async_mock_service(
        hass, media_player.DOMAIN, media_player.SERVICE_VOLUME_MUTE
    )
    await trt.execute(
        trait.COMMAND_MUTE,
        BASIC_DATA,
        {"mute": True},
        {},
    )
    assert len(mute_calls) == 1
    assert mute_calls[0].data == {
        ATTR_ENTITY_ID: "media_player.bla",
        media_player.ATTR_MEDIA_VOLUME_MUTED: True,
    }

    unmute_calls = async_mock_service(
        hass, media_player.DOMAIN, media_player.SERVICE_VOLUME_MUTE
    )
    await trt.execute(
        trait.COMMAND_MUTE,
        BASIC_DATA,
        {"mute": False},
        {},
    )
    assert len(unmute_calls) == 1
    assert unmute_calls[0].data == {
        ATTR_ENTITY_ID: "media_player.bla",
        media_player.ATTR_MEDIA_VOLUME_MUTED: False,
    }