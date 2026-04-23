async def test_async_update_playback_metadata(
    hass: HomeAssistant,
    integration: None,
    mock_mozart_client: AsyncMock,
) -> None:
    """Test _async_update_playback_metadata."""
    playback_metadata_callback = (
        mock_mozart_client.get_playback_metadata_notifications.call_args[0][0]
    )

    assert (states := hass.states.get(TEST_MEDIA_PLAYER_ENTITY_ID))
    assert ATTR_MEDIA_DURATION not in states.attributes
    assert ATTR_MEDIA_TITLE not in states.attributes
    assert ATTR_MEDIA_ALBUM_NAME not in states.attributes
    assert ATTR_MEDIA_ALBUM_ARTIST not in states.attributes
    assert ATTR_MEDIA_TRACK not in states.attributes
    assert ATTR_MEDIA_CHANNEL not in states.attributes
    assert ATTR_MEDIA_CONTENT_ID not in states.attributes

    # Send the WebSocket event dispatch
    playback_metadata_callback(TEST_PLAYBACK_METADATA)

    assert (states := hass.states.get(TEST_MEDIA_PLAYER_ENTITY_ID))
    assert (
        states.attributes[ATTR_MEDIA_DURATION]
        == TEST_PLAYBACK_METADATA.total_duration_seconds
    )
    assert states.attributes[ATTR_MEDIA_TITLE] == TEST_PLAYBACK_METADATA.title
    assert states.attributes[ATTR_MEDIA_ALBUM_NAME] == TEST_PLAYBACK_METADATA.album_name
    assert (
        states.attributes[ATTR_MEDIA_ALBUM_ARTIST] == TEST_PLAYBACK_METADATA.artist_name
    )
    assert states.attributes[ATTR_MEDIA_TRACK] == TEST_PLAYBACK_METADATA.track
    assert states.attributes[ATTR_MEDIA_CHANNEL] == TEST_PLAYBACK_METADATA.organization
    assert states.attributes[ATTR_MEDIA_CHANNEL] == TEST_PLAYBACK_METADATA.organization
    assert (
        states.attributes[ATTR_MEDIA_CONTENT_ID]
        == TEST_PLAYBACK_METADATA.source_internal_id
    )
    assert states.attributes[ATTR_MEDIA_CONTENT_TYPE] == MediaType.MUSIC