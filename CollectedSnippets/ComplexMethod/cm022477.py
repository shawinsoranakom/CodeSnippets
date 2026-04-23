async def test_volume_media_player_relative(hass: HomeAssistant) -> None:
    """Test volume trait support for relative-volume-only media players."""
    assert trait.VolumeTrait.supported(
        media_player.DOMAIN,
        MediaPlayerEntityFeature.VOLUME_STEP,
        None,
        None,
    )
    trt = trait.VolumeTrait(
        hass,
        State(
            "media_player.bla",
            media_player.STATE_PLAYING,
            {
                ATTR_ASSUMED_STATE: True,
                ATTR_SUPPORTED_FEATURES: MediaPlayerEntityFeature.VOLUME_STEP,
            },
        ),
        BASIC_CONFIG,
    )

    assert trt.sync_attributes() == {
        "volumeMaxLevel": 100,
        "levelStepSize": 10,
        "volumeCanMuteAndUnmute": False,
        "commandOnlyVolume": True,
    }

    assert trt.query_attributes() == {}

    calls = async_mock_service(
        hass, media_player.DOMAIN, media_player.SERVICE_VOLUME_UP
    )

    await trt.execute(
        trait.COMMAND_VOLUME_RELATIVE,
        BASIC_DATA,
        {"relativeSteps": 10},
        {},
    )
    assert len(calls) == 10
    for call in calls:
        assert call.data == {
            ATTR_ENTITY_ID: "media_player.bla",
        }

    calls = async_mock_service(
        hass, media_player.DOMAIN, media_player.SERVICE_VOLUME_DOWN
    )
    await trt.execute(
        trait.COMMAND_VOLUME_RELATIVE,
        BASIC_DATA,
        {"relativeSteps": -10},
        {},
    )
    assert len(calls) == 10
    for call in calls:
        assert call.data == {
            ATTR_ENTITY_ID: "media_player.bla",
        }

    with pytest.raises(SmartHomeError):
        await trt.execute(trait.COMMAND_SET_VOLUME, BASIC_DATA, {"volumeLevel": 42}, {})

    with pytest.raises(SmartHomeError):
        await trt.execute(trait.COMMAND_MUTE, BASIC_DATA, {"mute": True}, {})