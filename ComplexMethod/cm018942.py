async def test_lookup_media_with_urls(hass: HomeAssistant, mock_plex_server) -> None:
    """Test media lookup for media_player.play_media calls from cast/sonos."""
    CONTENT_ID_URL = f"{PLEX_URI_SCHEME}{DEFAULT_DATA[CONF_SERVER_IDENTIFIER]}/100"

    # Test URL format
    result = process_plex_payload(
        hass, MediaType.MUSIC, CONTENT_ID_URL, supports_playqueues=False
    )
    assert isinstance(result.media, plexapi.audio.Track)
    assert result.shuffle is False

    # Test URL format with shuffle
    CONTENT_ID_URL_WITH_SHUFFLE = CONTENT_ID_URL + "?shuffle=1"
    result = process_plex_payload(
        hass, MediaType.MUSIC, CONTENT_ID_URL_WITH_SHUFFLE, supports_playqueues=False
    )
    assert isinstance(result.media, plexapi.audio.Track)
    assert result.shuffle is True
    assert result.offset == 0

    # Test URL format with continuous
    CONTENT_ID_URL_WITH_CONTINUOUS = CONTENT_ID_URL + "?continuous=1"
    result = process_plex_payload(
        hass, MediaType.MUSIC, CONTENT_ID_URL_WITH_CONTINUOUS, supports_playqueues=False
    )
    assert isinstance(result.media, plexapi.audio.Track)
    assert result.continuous is True
    assert result.offset == 0