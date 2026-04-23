async def test_media_player_play_media_action(
    hass: HomeAssistant,
    music_assistant_client: MagicMock,
) -> None:
    """Test media_player (advanced) play_media action."""
    await setup_integration_from_fixtures(hass, music_assistant_client)
    entity_id = "media_player.test_player_1"
    mass_player_id = "00:00:00:00:00:01"
    state = hass.states.get(entity_id)
    assert state

    # test simple play_media call with URI as media_id and no media type
    await hass.services.async_call(
        DOMAIN,
        SERVICE_PLAY_MEDIA_ADVANCED,
        {
            ATTR_ENTITY_ID: entity_id,
            ATTR_MEDIA_ID: "spotify://track/1234",
        },
        blocking=True,
    )
    assert music_assistant_client.send_command.call_count == 1
    assert music_assistant_client.send_command.call_args == call(
        "player_queues/play_media",
        queue_id=mass_player_id,
        media=["spotify://track/1234"],
        option=None,
        radio_mode=False,
        start_item=None,
    )

    # test simple play_media call with URI and enqueue specified
    music_assistant_client.send_command.reset_mock()
    await hass.services.async_call(
        DOMAIN,
        SERVICE_PLAY_MEDIA_ADVANCED,
        {
            ATTR_ENTITY_ID: entity_id,
            ATTR_MEDIA_ID: "spotify://track/1234",
            ATTR_MEDIA_ENQUEUE: "add",
        },
        blocking=True,
    )
    assert music_assistant_client.send_command.call_count == 1
    assert music_assistant_client.send_command.call_args == call(
        "player_queues/play_media",
        queue_id=mass_player_id,
        media=["spotify://track/1234"],
        option=QueueOption.ADD,
        radio_mode=False,
        start_item=None,
    )

    # test basic play_media call with URL and radio mode specified
    music_assistant_client.send_command.reset_mock()
    await hass.services.async_call(
        DOMAIN,
        SERVICE_PLAY_MEDIA_ADVANCED,
        {
            ATTR_ENTITY_ID: entity_id,
            ATTR_MEDIA_ID: "spotify://track/1234",
            ATTR_RADIO_MODE: True,
        },
        blocking=True,
    )
    assert music_assistant_client.send_command.call_count == 1
    assert music_assistant_client.send_command.call_args == call(
        "player_queues/play_media",
        queue_id=mass_player_id,
        media=["spotify://track/1234"],
        option=None,
        radio_mode=True,
        start_item=None,
    )

    # test play_media call with media id and media type specified
    music_assistant_client.send_command.reset_mock()
    music_assistant_client.music.get_item = AsyncMock(return_value=MOCK_TRACK)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_PLAY_MEDIA_ADVANCED,
        {
            ATTR_ENTITY_ID: entity_id,
            ATTR_MEDIA_ID: "1",
            ATTR_MEDIA_TYPE: "track",
        },
        blocking=True,
    )
    assert music_assistant_client.music.get_item.call_count == 1
    assert music_assistant_client.music.get_item.call_args == call(
        MediaType.TRACK, "1", "library"
    )
    assert music_assistant_client.send_command.call_count == 1
    assert music_assistant_client.send_command.call_args == call(
        "player_queues/play_media",
        queue_id=mass_player_id,
        media=[MOCK_TRACK.uri],
        option=None,
        radio_mode=False,
        start_item=None,
    )

    # test play_media call by name
    music_assistant_client.send_command.reset_mock()
    music_assistant_client.music.get_item_by_name = AsyncMock(return_value=MOCK_TRACK)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_PLAY_MEDIA_ADVANCED,
        {
            ATTR_ENTITY_ID: entity_id,
            ATTR_MEDIA_ID: "test",
            ATTR_ARTIST: "artist",
            ATTR_ALBUM: "album",
        },
        blocking=True,
    )
    assert music_assistant_client.music.get_item_by_name.call_count == 1
    assert music_assistant_client.music.get_item_by_name.call_args == call(
        name="test",
        artist="artist",
        album="album",
        media_type=None,
    )
    assert music_assistant_client.send_command.call_count == 1
    assert music_assistant_client.send_command.call_args == call(
        "player_queues/play_media",
        queue_id=mass_player_id,
        media=[MOCK_TRACK.uri],
        option=None,
        radio_mode=False,
        start_item=None,
    )