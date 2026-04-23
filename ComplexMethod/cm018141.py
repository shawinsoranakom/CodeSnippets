async def test_entity_supported_features(
    hass: HomeAssistant,
    mock_stream_magic_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test entity attributes."""
    await setup_integration(hass, mock_config_entry)
    await mock_state_update(mock_stream_magic_client)
    await hass.async_block_till_done()

    state = hass.states.get(ENTITY_ID)
    attrs = state.attributes

    # Ensure volume isn't available when pre-amp is disabled
    assert not mock_stream_magic_client.state.pre_amp_mode
    assert (
        MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_STEP
        | MediaPlayerEntityFeature.VOLUME_MUTE
        not in attrs[ATTR_SUPPORTED_FEATURES]
    )

    # Check for basic media controls
    assert {
        TransportControl.PLAY_PAUSE,
        TransportControl.TRACK_NEXT,
        TransportControl.TRACK_PREVIOUS,
    }.issubset(mock_stream_magic_client.now_playing.controls)
    assert (
        MediaPlayerEntityFeature.PLAY
        | MediaPlayerEntityFeature.PAUSE
        | MediaPlayerEntityFeature.NEXT_TRACK
        | MediaPlayerEntityFeature.PREVIOUS_TRACK
        in attrs[ATTR_SUPPORTED_FEATURES]
    )
    assert (
        MediaPlayerEntityFeature.SHUFFLE_SET
        | MediaPlayerEntityFeature.REPEAT_SET
        | MediaPlayerEntityFeature.SEEK
        not in attrs[ATTR_SUPPORTED_FEATURES]
    )

    mock_stream_magic_client.now_playing.controls = [
        TransportControl.TOGGLE_REPEAT,
        TransportControl.TOGGLE_SHUFFLE,
        TransportControl.SEEK,
    ]
    await mock_state_update(mock_stream_magic_client)
    await hass.async_block_till_done()

    state = hass.states.get(ENTITY_ID)
    attrs = state.attributes

    assert (
        MediaPlayerEntityFeature.SHUFFLE_SET
        | MediaPlayerEntityFeature.REPEAT_SET
        | MediaPlayerEntityFeature.SEEK
        in attrs[ATTR_SUPPORTED_FEATURES]
    )

    mock_stream_magic_client.state.pre_amp_mode = True
    await mock_state_update(mock_stream_magic_client)
    await hass.async_block_till_done()

    state = hass.states.get(ENTITY_ID)
    attrs = state.attributes
    assert (
        MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_STEP
        | MediaPlayerEntityFeature.VOLUME_MUTE
        in attrs[ATTR_SUPPORTED_FEATURES]
    )