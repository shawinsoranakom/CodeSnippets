async def test_async_update_source_change(
    hass: HomeAssistant,
    integration: None,
    mock_mozart_client: AsyncMock,
    source: Source,
    content_type: MediaType,
    progress: int,
    metadata: PlaybackContentMetadata,
    content_id_available: bool,
) -> None:
    """Test _async_update_source_change."""
    playback_progress_callback = (
        mock_mozart_client.get_playback_progress_notifications.call_args[0][0]
    )
    playback_metadata_callback = (
        mock_mozart_client.get_playback_metadata_notifications.call_args[0][0]
    )
    source_change_callback = (
        mock_mozart_client.get_source_change_notifications.call_args[0][0]
    )

    assert (states := hass.states.get(TEST_MEDIA_PLAYER_ENTITY_ID))
    assert ATTR_INPUT_SOURCE not in states.attributes
    assert states.attributes[ATTR_MEDIA_CONTENT_TYPE] == MediaType.MUSIC

    # Simulate progress attribute being available
    playback_progress_callback(TEST_PLAYBACK_PROGRESS)

    # Simulate metadata
    playback_metadata_callback(metadata)
    source_change_callback(source)

    assert (states := hass.states.get(TEST_MEDIA_PLAYER_ENTITY_ID))
    assert states.attributes[ATTR_INPUT_SOURCE] == source.name
    assert states.attributes[ATTR_MEDIA_CONTENT_TYPE] == content_type
    assert states.attributes[ATTR_MEDIA_POSITION] == progress
    assert (ATTR_MEDIA_CONTENT_ID in states.attributes) == content_id_available