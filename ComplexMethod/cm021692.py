async def test_media_player_supported_features(
    hass: HomeAssistant,
    music_assistant_client: MagicMock,
) -> None:
    """Test if media_player entity supported features are cortrectly (re)mapped."""
    await setup_integration_from_fixtures(hass, music_assistant_client)
    entity_id = "media_player.test_player_1"
    mass_player_id = "00:00:00:00:00:01"
    state = hass.states.get(entity_id)
    assert state
    expected_features = (
        MediaPlayerEntityFeature.STOP
        | MediaPlayerEntityFeature.PREVIOUS_TRACK
        | MediaPlayerEntityFeature.NEXT_TRACK
        | MediaPlayerEntityFeature.SHUFFLE_SET
        | MediaPlayerEntityFeature.REPEAT_SET
        | MediaPlayerEntityFeature.PLAY
        | MediaPlayerEntityFeature.PLAY_MEDIA
        | MediaPlayerEntityFeature.VOLUME_STEP
        | MediaPlayerEntityFeature.CLEAR_PLAYLIST
        | MediaPlayerEntityFeature.BROWSE_MEDIA
        | MediaPlayerEntityFeature.MEDIA_ENQUEUE
        | MediaPlayerEntityFeature.MEDIA_ANNOUNCE
        | MediaPlayerEntityFeature.SEEK
        | MediaPlayerEntityFeature.PAUSE
        | MediaPlayerEntityFeature.GROUPING
        | MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_STEP
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.SEARCH_MEDIA
        | MediaPlayerEntityFeature.SELECT_SOURCE
        | MediaPlayerEntityFeature.SELECT_SOUND_MODE
    )
    assert state.attributes["supported_features"] == expected_features
    # remove power control capability from player, trigger subscription callback
    # and check if the supported features got updated
    music_assistant_client.players._players[
        mass_player_id
    ].power_control = PLAYER_CONTROL_NONE
    await trigger_subscription_callback(
        hass, music_assistant_client, EventType.PLAYER_CONFIG_UPDATED, mass_player_id
    )
    expected_features &= ~MediaPlayerEntityFeature.TURN_ON
    expected_features &= ~MediaPlayerEntityFeature.TURN_OFF
    state = hass.states.get(entity_id)
    assert state
    assert state.attributes["supported_features"] == expected_features

    # remove volume control capability from player, trigger subscription callback
    # and check if the supported features got updated
    music_assistant_client.players._players[
        mass_player_id
    ].volume_control = PLAYER_CONTROL_NONE
    await trigger_subscription_callback(
        hass, music_assistant_client, EventType.PLAYER_CONFIG_UPDATED, mass_player_id
    )
    expected_features &= ~MediaPlayerEntityFeature.VOLUME_SET
    expected_features &= ~MediaPlayerEntityFeature.VOLUME_STEP
    state = hass.states.get(entity_id)
    assert state
    assert state.attributes["supported_features"] == expected_features

    # remove mute control capability from player, trigger subscription callback
    # and check if the supported features got updated
    music_assistant_client.players._players[
        mass_player_id
    ].mute_control = PLAYER_CONTROL_NONE
    await trigger_subscription_callback(
        hass, music_assistant_client, EventType.PLAYER_CONFIG_UPDATED, mass_player_id
    )
    expected_features &= ~MediaPlayerEntityFeature.VOLUME_MUTE
    state = hass.states.get(entity_id)
    assert state
    assert state.attributes["supported_features"] == expected_features

    # remove grouping capability from player, trigger subscription callback
    # and check if the supported features got updated
    music_assistant_client.players._players[mass_player_id].supported_features.remove(
        PlayerFeature.SET_MEMBERS
    )
    await trigger_subscription_callback(
        hass, music_assistant_client, EventType.PLAYER_CONFIG_UPDATED, mass_player_id
    )
    expected_features &= ~MediaPlayerEntityFeature.GROUPING
    state = hass.states.get(entity_id)
    assert state
    assert state.attributes["supported_features"] == expected_features