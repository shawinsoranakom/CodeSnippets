async def test_transport_control(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Test the TransportControlTrait."""
    assert helpers.get_google_type(media_player.DOMAIN, None) is not None

    for feature in trait.MEDIA_COMMAND_SUPPORT_MAPPING.values():
        assert trait.TransportControlTrait.supported(
            media_player.DOMAIN, feature, None, None
        )

    now = datetime(2020, 1, 1, tzinfo=dt_util.UTC)

    trt = trait.TransportControlTrait(
        hass,
        State(
            "media_player.bla",
            media_player.STATE_PLAYING,
            {
                media_player.ATTR_MEDIA_POSITION: 100,
                media_player.ATTR_MEDIA_DURATION: 200,
                media_player.ATTR_MEDIA_POSITION_UPDATED_AT: now
                - timedelta(seconds=10),
                media_player.ATTR_MEDIA_VOLUME_LEVEL: 0.5,
                ATTR_SUPPORTED_FEATURES: MediaPlayerEntityFeature.PLAY
                | MediaPlayerEntityFeature.STOP,
            },
        ),
        BASIC_CONFIG,
    )

    assert trt.sync_attributes() == {
        "transportControlSupportedCommands": ["RESUME", "STOP"]
    }
    assert trt.query_attributes() == {}

    # COMMAND_MEDIA_SEEK_RELATIVE
    calls = async_mock_service(
        hass, media_player.DOMAIN, media_player.SERVICE_MEDIA_SEEK
    )

    # Patch to avoid time ticking over during the command failing the test
    freezer.move_to(now)
    await trt.execute(
        trait.COMMAND_MEDIA_SEEK_RELATIVE,
        BASIC_DATA,
        {"relativePositionMs": 10000},
        {},
    )
    assert len(calls) == 1
    assert calls[0].data == {
        ATTR_ENTITY_ID: "media_player.bla",
        # 100s (current position) + 10s (from command) + 10s (from updated_at)
        media_player.ATTR_MEDIA_SEEK_POSITION: 120,
    }

    # COMMAND_MEDIA_SEEK_TO_POSITION
    calls = async_mock_service(
        hass, media_player.DOMAIN, media_player.SERVICE_MEDIA_SEEK
    )
    await trt.execute(
        trait.COMMAND_MEDIA_SEEK_TO_POSITION, BASIC_DATA, {"absPositionMs": 50000}, {}
    )
    assert len(calls) == 1
    assert calls[0].data == {
        ATTR_ENTITY_ID: "media_player.bla",
        media_player.ATTR_MEDIA_SEEK_POSITION: 50,
    }

    # COMMAND_MEDIA_NEXT
    calls = async_mock_service(
        hass, media_player.DOMAIN, media_player.SERVICE_MEDIA_NEXT_TRACK
    )
    await trt.execute(trait.COMMAND_MEDIA_NEXT, BASIC_DATA, {}, {})
    assert len(calls) == 1
    assert calls[0].data == {ATTR_ENTITY_ID: "media_player.bla"}

    # COMMAND_MEDIA_PAUSE
    calls = async_mock_service(
        hass, media_player.DOMAIN, media_player.SERVICE_MEDIA_PAUSE
    )
    await trt.execute(trait.COMMAND_MEDIA_PAUSE, BASIC_DATA, {}, {})
    assert len(calls) == 1
    assert calls[0].data == {ATTR_ENTITY_ID: "media_player.bla"}

    # COMMAND_MEDIA_PREVIOUS
    calls = async_mock_service(
        hass, media_player.DOMAIN, media_player.SERVICE_MEDIA_PREVIOUS_TRACK
    )
    await trt.execute(trait.COMMAND_MEDIA_PREVIOUS, BASIC_DATA, {}, {})
    assert len(calls) == 1
    assert calls[0].data == {ATTR_ENTITY_ID: "media_player.bla"}

    # COMMAND_MEDIA_RESUME
    calls = async_mock_service(
        hass, media_player.DOMAIN, media_player.SERVICE_MEDIA_PLAY
    )
    await trt.execute(trait.COMMAND_MEDIA_RESUME, BASIC_DATA, {}, {})
    assert len(calls) == 1
    assert calls[0].data == {ATTR_ENTITY_ID: "media_player.bla"}

    # COMMAND_MEDIA_SHUFFLE
    calls = async_mock_service(
        hass, media_player.DOMAIN, media_player.SERVICE_SHUFFLE_SET
    )
    await trt.execute(trait.COMMAND_MEDIA_SHUFFLE, BASIC_DATA, {}, {})
    assert len(calls) == 1
    assert calls[0].data == {
        ATTR_ENTITY_ID: "media_player.bla",
        media_player.ATTR_MEDIA_SHUFFLE: True,
    }

    # COMMAND_MEDIA_STOP
    calls = async_mock_service(
        hass, media_player.DOMAIN, media_player.SERVICE_MEDIA_STOP
    )
    await trt.execute(trait.COMMAND_MEDIA_STOP, BASIC_DATA, {}, {})
    assert len(calls) == 1
    assert calls[0].data == {ATTR_ENTITY_ID: "media_player.bla"}