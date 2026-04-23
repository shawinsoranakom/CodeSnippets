async def test_state_machine_updates_from_device_callbacks(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_wiim_device: MagicMock,
    mock_wiim_controller: MagicMock,
) -> None:
    """Test cached device state is reflected in Home Assistant."""
    await setup_integration(hass, mock_config_entry)
    state = hass.states.get(MEDIA_PLAYER_ENTITY_ID)
    assert state.state == MediaPlayerState.IDLE
    assert state.attributes[ATTR_MEDIA_VOLUME_LEVEL] == 0.5
    assert state.attributes[ATTR_INPUT_SOURCE] == "Network"
    assert state.attributes["supported_features"] == int(
        MediaPlayerEntityFeature.PLAY
        | MediaPlayerEntityFeature.PAUSE
        | MediaPlayerEntityFeature.STOP
        | MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.BROWSE_MEDIA
        | MediaPlayerEntityFeature.PLAY_MEDIA
        | MediaPlayerEntityFeature.SELECT_SOURCE
        | MediaPlayerEntityFeature.SEEK
    )

    mock_wiim_device.volume = 60
    mock_wiim_device.playing_status = PlayingStatus.PLAYING
    mock_wiim_device.play_mode = "Bluetooth"
    mock_wiim_device.output_mode = "optical"
    mock_wiim_device.loop_state = WiimLoopState(
        repeat=WiimRepeatMode.ALL,
        shuffle=True,
    )
    mock_wiim_device.current_media = WiimMediaMetadata(
        title="New Song",
        artist="Test Artist",
        album="Test Album",
        uri="http://example.com/song.flac",
        duration=180,
        position=42,
    )
    mock_wiim_device.async_get_transport_capabilities.return_value = (
        WiimTransportCapabilities(
            can_next=True,
            can_previous=False,
            can_repeat=True,
            can_shuffle=True,
        )
    )

    await fire_general_update(hass, mock_wiim_device)

    state = hass.states.get(MEDIA_PLAYER_ENTITY_ID)
    assert state.state == MediaPlayerState.PLAYING
    assert state.attributes[ATTR_MEDIA_TITLE] == "New Song"
    assert state.attributes[ATTR_MEDIA_ALBUM_NAME] == "Test Album"
    assert state.attributes[ATTR_MEDIA_DURATION] == 180
    assert state.attributes[ATTR_MEDIA_POSITION] == 42
    assert state.attributes[ATTR_MEDIA_VOLUME_LEVEL] == 0.6
    assert state.attributes[ATTR_INPUT_SOURCE] == "Bluetooth"
    assert state.attributes[ATTR_MEDIA_REPEAT] == RepeatMode.ALL
    assert state.attributes[ATTR_MEDIA_SHUFFLE] is True
    assert state.attributes["supported_features"] == int(
        MediaPlayerEntityFeature.PLAY
        | MediaPlayerEntityFeature.PAUSE
        | MediaPlayerEntityFeature.STOP
        | MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.BROWSE_MEDIA
        | MediaPlayerEntityFeature.PLAY_MEDIA
        | MediaPlayerEntityFeature.SELECT_SOURCE
        | MediaPlayerEntityFeature.SEEK
        | MediaPlayerEntityFeature.NEXT_TRACK
        | MediaPlayerEntityFeature.REPEAT_SET
        | MediaPlayerEntityFeature.SHUFFLE_SET
    )