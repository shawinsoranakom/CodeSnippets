async def test_async_update_source_change_video(
    hass: HomeAssistant,
    integration: None,
    mock_mozart_client: AsyncMock,
) -> None:
    """Test _async_update_source_change with a video source."""
    playback_metadata_callback = (
        mock_mozart_client.get_playback_metadata_notifications.call_args[0][0]
    )
    source_change_callback = (
        mock_mozart_client.get_source_change_notifications.call_args[0][0]
    )

    assert (states := hass.states.get(TEST_MEDIA_PLAYER_ENTITY_ID))
    assert ATTR_INPUT_SOURCE not in states.attributes
    assert states.attributes[ATTR_MEDIA_CONTENT_TYPE] == MediaType.MUSIC

    # Simulate metadata and source change
    playback_metadata_callback(TEST_PLAYBACK_METADATA_VIDEO)
    source_change_callback(Source(id="tv", name="TV"))

    assert (states := hass.states.get(TEST_MEDIA_PLAYER_ENTITY_ID))
    assert states.attributes[ATTR_INPUT_SOURCE] == TEST_PLAYBACK_METADATA_VIDEO.title
    assert states.attributes[ATTR_MEDIA_CONTENT_TYPE] == BeoMediaType.TV
    assert (
        states.attributes[ATTR_MEDIA_CONTENT_ID]
        == TEST_PLAYBACK_METADATA_VIDEO.source_internal_id
    )