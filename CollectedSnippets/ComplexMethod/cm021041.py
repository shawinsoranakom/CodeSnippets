async def test_media_player_formats_reload_preserves_data(
    hass: HomeAssistant,
    mock_client: APIClient,
    mock_esphome_device: MockESPHomeDeviceType,
) -> None:
    """Test that media player formats are properly managed on reload."""
    # Create a media player with supported formats
    supported_formats = [
        MediaPlayerSupportedFormat(
            format="mp3",
            sample_rate=48000,
            num_channels=2,
            purpose=MediaPlayerFormatPurpose.DEFAULT,
        ),
        MediaPlayerSupportedFormat(
            format="wav",
            sample_rate=16000,
            num_channels=1,
            purpose=MediaPlayerFormatPurpose.ANNOUNCEMENT,
            sample_bytes=2,
        ),
    ]

    mock_device = await mock_esphome_device(
        mock_client=mock_client,
        entity_info=[
            MediaPlayerInfo(
                object_id="test_media_player",
                key=1,
                name="Test Media Player",
                supports_pause=True,
                # PLAY_MEDIA,BROWSE_MEDIA,STOP,VOLUME_SET,VOLUME_MUTE,MEDIA_ANNOUNCE,PAUSE,PLAY
                feature_flags=1200653,
                supported_formats=supported_formats,
            )
        ],
        states=[
            MediaPlayerEntityState(
                key=1, volume=50, muted=False, state=MediaPlayerState.IDLE
            )
        ],
    )
    await hass.async_block_till_done()

    # Verify entity was created
    state = hass.states.get("media_player.test_Test_Media_Player")
    assert state is not None
    assert state.state == "idle"

    # Test that play_media works with proxy URL (which requires formats to be stored)
    media_url = "http://127.0.0.1/test.mp3"

    await hass.services.async_call(
        MEDIA_PLAYER_DOMAIN,
        SERVICE_PLAY_MEDIA,
        {
            ATTR_ENTITY_ID: "media_player.test_Test_Media_Player",
            ATTR_MEDIA_CONTENT_TYPE: MediaType.MUSIC,
            ATTR_MEDIA_CONTENT_ID: media_url,
        },
        blocking=True,
    )

    # Verify the API was called with a proxy URL (contains /api/esphome/ffmpeg_proxy/)
    mock_client.media_player_command.assert_called_once()
    call_args = mock_client.media_player_command.call_args
    assert "/api/esphome/ffmpeg_proxy/" in call_args.kwargs["media_url"]
    assert ".mp3" in call_args.kwargs["media_url"]  # Should use mp3 format for default
    assert call_args.kwargs["announcement"] is None

    mock_client.media_player_command.reset_mock()

    # Reload the integration
    await hass.config_entries.async_reload(mock_device.entry.entry_id)
    await hass.async_block_till_done()

    # Verify entity still exists after reload
    state = hass.states.get("media_player.test_Test_Media_Player")
    assert state is not None

    # Test that play_media still works after reload with announcement
    await hass.services.async_call(
        MEDIA_PLAYER_DOMAIN,
        SERVICE_PLAY_MEDIA,
        {
            ATTR_ENTITY_ID: "media_player.test_Test_Media_Player",
            ATTR_MEDIA_CONTENT_TYPE: MediaType.MUSIC,
            ATTR_MEDIA_CONTENT_ID: media_url,
            ATTR_MEDIA_ANNOUNCE: True,
        },
        blocking=True,
    )

    # Verify the API was called with a proxy URL using wav format for announcements
    mock_client.media_player_command.assert_called_once()
    call_args = mock_client.media_player_command.call_args
    assert "/api/esphome/ffmpeg_proxy/" in call_args.kwargs["media_url"]
    assert (
        ".wav" in call_args.kwargs["media_url"]
    )  # Should use wav format for announcement
    assert call_args.kwargs["announcement"] is True