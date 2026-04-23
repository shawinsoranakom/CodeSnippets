async def test_mute_requires_both_commands(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    init_integration: MockConfigEntry,
    mock_jellyfin: MagicMock,
    mock_api: MagicMock,
) -> None:
    """Test that VOLUME_MUTE requires both Mute AND Unmute commands."""

    # SESSION-UUID-FIVE has only Mute (no Unmute) - should NOT have VOLUME_MUTE
    state_five = hass.states.get("media_player.jellyfin_device_five")
    assert state_five

    entity_five = hass.data["entity_components"]["media_player"].get_entity(
        state_five.entity_id
    )
    features_five = entity_five.supported_features

    # Should NOT have mute feature
    assert not (features_five & MediaPlayerEntityFeature.VOLUME_MUTE)
    # But should still have other features
    assert features_five & MediaPlayerEntityFeature.PLAY
    assert features_five & MediaPlayerEntityFeature.VOLUME_SET

    # SESSION-UUID-SIX has only Unmute (no Mute) - should NOT have VOLUME_MUTE
    state_six = hass.states.get("media_player.jellyfin_device_six")
    assert state_six

    entity_six = hass.data["entity_components"]["media_player"].get_entity(
        state_six.entity_id
    )
    features_six = entity_six.supported_features

    # Should NOT have mute feature
    assert not (features_six & MediaPlayerEntityFeature.VOLUME_MUTE)
    # But should still have other features
    assert features_six & MediaPlayerEntityFeature.PLAY
    assert features_six & MediaPlayerEntityFeature.VOLUME_SET