async def test_async_update_playback_progress(
    hass: HomeAssistant,
    integration: None,
    mock_mozart_client: AsyncMock,
) -> None:
    """Test _async_update_playback_progress."""
    playback_progress_callback = (
        mock_mozart_client.get_playback_progress_notifications.call_args[0][0]
    )

    assert (states := hass.states.get(TEST_MEDIA_PLAYER_ENTITY_ID))
    assert ATTR_MEDIA_POSITION not in states.attributes
    old_updated_at = states.attributes[ATTR_MEDIA_POSITION_UPDATED_AT]
    assert old_updated_at

    playback_progress_callback(TEST_PLAYBACK_PROGRESS)

    assert (states := hass.states.get(TEST_MEDIA_PLAYER_ENTITY_ID))
    assert states.attributes[ATTR_MEDIA_POSITION] == TEST_PLAYBACK_PROGRESS.progress
    new_updated_at = states.attributes[ATTR_MEDIA_POSITION_UPDATED_AT]
    assert new_updated_at
    assert old_updated_at != new_updated_at