async def test_attributes(
    hass: HomeAssistant, dmr_device_mock: Mock, mock_entity_id: str
) -> None:
    """Test attributes of a connected DlnaDmrEntity."""
    # Check attributes come directly from the device
    attrs = await get_attrs(hass, mock_entity_id)
    assert attrs[mp.ATTR_MEDIA_VOLUME_LEVEL] is dmr_device_mock.volume_level
    assert attrs[mp.ATTR_MEDIA_VOLUME_MUTED] is dmr_device_mock.is_volume_muted
    assert attrs[mp.ATTR_MEDIA_DURATION] is dmr_device_mock.media_duration
    assert attrs[mp.ATTR_MEDIA_POSITION] is dmr_device_mock.media_position
    assert (
        attrs[mp.ATTR_MEDIA_POSITION_UPDATED_AT]
        is dmr_device_mock.media_position_updated_at
    )
    assert attrs[mp.ATTR_MEDIA_CONTENT_ID] is dmr_device_mock.current_track_uri
    assert attrs[mp.ATTR_MEDIA_ARTIST] is dmr_device_mock.media_artist
    assert attrs[mp.ATTR_MEDIA_ALBUM_NAME] is dmr_device_mock.media_album_name
    assert attrs[mp.ATTR_MEDIA_ALBUM_ARTIST] is dmr_device_mock.media_album_artist
    assert attrs[mp.ATTR_MEDIA_TRACK] is dmr_device_mock.media_track_number
    assert attrs[mp.ATTR_MEDIA_SERIES_TITLE] is dmr_device_mock.media_series_title
    assert attrs[mp.ATTR_MEDIA_SEASON] is dmr_device_mock.media_season_number
    assert attrs[mp.ATTR_MEDIA_EPISODE] is dmr_device_mock.media_episode_number
    assert attrs[mp.ATTR_MEDIA_CHANNEL] is dmr_device_mock.media_channel_name
    assert attrs[mp.ATTR_SOUND_MODE_LIST] is dmr_device_mock.preset_names

    # Entity picture is cached, won't correspond to remote image
    assert isinstance(attrs[ha_const.ATTR_ENTITY_PICTURE], str)

    # media_title depends on what is available
    assert attrs[mp.ATTR_MEDIA_TITLE] is dmr_device_mock.media_program_title
    dmr_device_mock.media_program_title = None
    attrs = await get_attrs(hass, mock_entity_id)
    assert attrs[mp.ATTR_MEDIA_TITLE] is dmr_device_mock.media_title

    # media_content_type is mapped from UPnP class to MediaPlayer type
    dmr_device_mock.media_class = "object.item.audioItem.musicTrack"
    attrs = await get_attrs(hass, mock_entity_id)
    assert attrs[mp.ATTR_MEDIA_CONTENT_TYPE] == MediaType.MUSIC
    dmr_device_mock.media_class = "object.item.videoItem.movie"
    attrs = await get_attrs(hass, mock_entity_id)
    assert attrs[mp.ATTR_MEDIA_CONTENT_TYPE] == MediaType.MOVIE
    dmr_device_mock.media_class = "object.item.videoItem.videoBroadcast"
    attrs = await get_attrs(hass, mock_entity_id)
    assert attrs[mp.ATTR_MEDIA_CONTENT_TYPE] == MediaType.TVSHOW

    # media_season & media_episode have a special case
    dmr_device_mock.media_season_number = "0"
    dmr_device_mock.media_episode_number = "123"
    attrs = await get_attrs(hass, mock_entity_id)
    assert attrs[mp.ATTR_MEDIA_SEASON] == "1"
    assert attrs[mp.ATTR_MEDIA_EPISODE] == "23"
    dmr_device_mock.media_season_number = "0"
    dmr_device_mock.media_episode_number = "S1E23"  # Unexpected and not parsed
    attrs = await get_attrs(hass, mock_entity_id)
    assert attrs[mp.ATTR_MEDIA_SEASON] == "0"
    assert attrs[mp.ATTR_MEDIA_EPISODE] == "S1E23"

    # shuffle and repeat is based on device's play mode
    for play_mode, shuffle, repeat in (
        (PlayMode.NORMAL, False, RepeatMode.OFF),
        (PlayMode.SHUFFLE, True, RepeatMode.OFF),
        (PlayMode.REPEAT_ONE, False, RepeatMode.ONE),
        (PlayMode.REPEAT_ALL, False, RepeatMode.ALL),
        (PlayMode.RANDOM, True, RepeatMode.ALL),
        (PlayMode.DIRECT_1, False, RepeatMode.OFF),
        (PlayMode.INTRO, False, RepeatMode.OFF),
    ):
        dmr_device_mock.play_mode = play_mode
        attrs = await get_attrs(hass, mock_entity_id)
        assert attrs[mp.ATTR_MEDIA_SHUFFLE] is shuffle
        assert attrs[mp.ATTR_MEDIA_REPEAT] == repeat
    for bad_play_mode in (None, PlayMode.VENDOR_DEFINED):
        dmr_device_mock.play_mode = bad_play_mode
        attrs = await get_attrs(hass, mock_entity_id)
        assert mp.ATTR_MEDIA_SHUFFLE not in attrs
        assert mp.ATTR_MEDIA_REPEAT not in attrs