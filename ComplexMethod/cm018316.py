async def test_supports_media_control_fallback(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    init_integration: MockConfigEntry,
    mock_jellyfin: MagicMock,
    mock_api: MagicMock,
) -> None:
    """Test that SupportsMediaControl enables controls without PlayMediaSource."""
    # SESSION-UUID-TWO has SupportsMediaControl: true but no PlayMediaSource command
    state = hass.states.get("media_player.jellyfin_device_two")

    assert state
    assert state.state == MediaPlayerState.PLAYING

    entry = entity_registry.async_get(state.entity_id)
    assert entry

    # Get the entity to check supported features
    entity = hass.data["entity_components"]["media_player"].get_entity(state.entity_id)
    features = entity.supported_features

    # Should have basic playback controls
    assert features & MediaPlayerEntityFeature.PLAY
    assert features & MediaPlayerEntityFeature.PAUSE
    assert features & MediaPlayerEntityFeature.STOP
    assert features & MediaPlayerEntityFeature.SEEK
    assert features & MediaPlayerEntityFeature.BROWSE_MEDIA
    assert features & MediaPlayerEntityFeature.PLAY_MEDIA
    assert features & MediaPlayerEntityFeature.MEDIA_ENQUEUE

    # Should also have volume controls since it has VolumeSet, Mute, and Unmute
    assert features & MediaPlayerEntityFeature.VOLUME_SET
    assert features & MediaPlayerEntityFeature.VOLUME_MUTE