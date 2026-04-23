async def test_volume_media_player(hass: HomeAssistant) -> None:
    """Test volume trait support for media player domain."""
    assert helpers.get_google_type(media_player.DOMAIN, None) is not None
    assert trait.VolumeTrait.supported(
        media_player.DOMAIN,
        MediaPlayerEntityFeature.VOLUME_SET,
        None,
        None,
    )

    trt = trait.VolumeTrait(
        hass,
        State(
            "media_player.bla",
            media_player.STATE_PLAYING,
            {
                ATTR_SUPPORTED_FEATURES: MediaPlayerEntityFeature.VOLUME_SET,
                media_player.ATTR_MEDIA_VOLUME_LEVEL: 0.3,
            },
        ),
        BASIC_CONFIG,
    )

    assert trt.sync_attributes() == {
        "volumeMaxLevel": 100,
        "levelStepSize": 10,
        "volumeCanMuteAndUnmute": False,
        "commandOnlyVolume": False,
    }

    assert trt.query_attributes() == {"currentVolume": 30}

    calls = async_mock_service(
        hass, media_player.DOMAIN, media_player.SERVICE_VOLUME_SET
    )
    await trt.execute(trait.COMMAND_SET_VOLUME, BASIC_DATA, {"volumeLevel": 60}, {})
    assert len(calls) == 1
    assert calls[0].data == {
        ATTR_ENTITY_ID: "media_player.bla",
        media_player.ATTR_MEDIA_VOLUME_LEVEL: 0.6,
    }

    calls = async_mock_service(
        hass, media_player.DOMAIN, media_player.SERVICE_VOLUME_SET
    )
    await trt.execute(
        trait.COMMAND_VOLUME_RELATIVE, BASIC_DATA, {"relativeSteps": 10}, {}
    )
    assert len(calls) == 1
    assert calls[0].data == {
        ATTR_ENTITY_ID: "media_player.bla",
        media_player.ATTR_MEDIA_VOLUME_LEVEL: 0.4,
    }