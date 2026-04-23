async def test_volume_relative_media_player_intent(
    hass: HomeAssistant, direction: str, volume_change: float, volume_change_int: int
) -> None:
    """Test relative volume intents for media players."""
    assert await async_setup_component(hass, DOMAIN, {})
    await media_player_intent.async_setup_intents(hass)

    component: EntityComponent[MediaPlayerEntity] = hass.data[DOMAIN]

    default_volume = 0.5

    class VolumeTestMediaPlayer(MediaPlayerEntity):
        _attr_supported_features = MediaPlayerEntityFeature.VOLUME_SET
        _attr_volume_level = default_volume
        _attr_volume_step = 0.1
        _attr_state = MediaPlayerState.IDLE

        async def async_set_volume_level(self, volume):
            self._attr_volume_level = volume

    idle_entity = VolumeTestMediaPlayer()
    idle_entity.hass = hass
    idle_entity.platform = MockEntityPlatform(hass)
    idle_entity.entity_id = f"{DOMAIN}.idle_media_player"
    await component.async_add_entities([idle_entity])

    hass.states.async_set(
        idle_entity.entity_id,
        STATE_IDLE,
        attributes={
            ATTR_SUPPORTED_FEATURES: MediaPlayerEntityFeature.VOLUME_SET,
            ATTR_FRIENDLY_NAME: "Idle Media Player",
        },
    )

    idle_expected_volume = default_volume

    # Only 1 media player is present, so it's targeted even though its idle
    assert idle_entity.volume_level is not None
    assert math.isclose(idle_entity.volume_level, idle_expected_volume)
    response = await intent.async_handle(
        hass,
        "test",
        media_player_intent.INTENT_SET_VOLUME_RELATIVE,
        {"volume_step": {"value": direction}},
    )
    await hass.async_block_till_done()

    assert response.response_type == intent.IntentResponseType.ACTION_DONE
    idle_expected_volume += volume_change
    assert math.isclose(idle_entity.volume_level, idle_expected_volume)

    # Multiple media players (playing one should be targeted)
    playing_entity = VolumeTestMediaPlayer()
    playing_entity.hass = hass
    playing_entity.platform = MockEntityPlatform(hass)
    playing_entity.entity_id = f"{DOMAIN}.playing_media_player"
    await component.async_add_entities([playing_entity])

    hass.states.async_set(
        playing_entity.entity_id,
        STATE_PLAYING,
        attributes={
            ATTR_SUPPORTED_FEATURES: MediaPlayerEntityFeature.VOLUME_SET,
            ATTR_FRIENDLY_NAME: "Playing Media Player",
        },
    )

    playing_expected_volume = default_volume
    assert playing_entity.volume_level is not None
    assert math.isclose(playing_entity.volume_level, playing_expected_volume)
    response = await intent.async_handle(
        hass,
        "test",
        media_player_intent.INTENT_SET_VOLUME_RELATIVE,
        {"volume_step": {"value": direction}},
    )
    await hass.async_block_till_done()

    assert response.response_type == intent.IntentResponseType.ACTION_DONE
    playing_expected_volume += volume_change
    assert math.isclose(idle_entity.volume_level, idle_expected_volume)
    assert math.isclose(playing_entity.volume_level, playing_expected_volume)

    # We can still target by name even if the media player is idle
    response = await intent.async_handle(
        hass,
        "test",
        media_player_intent.INTENT_SET_VOLUME_RELATIVE,
        {"volume_step": {"value": direction}, "name": {"value": "Idle media player"}},
    )
    await hass.async_block_till_done()

    assert response.response_type == intent.IntentResponseType.ACTION_DONE
    idle_expected_volume += volume_change
    assert math.isclose(idle_entity.volume_level, idle_expected_volume)
    assert math.isclose(playing_entity.volume_level, playing_expected_volume)

    # Set relative volume by percent
    response = await intent.async_handle(
        hass,
        "test",
        media_player_intent.INTENT_SET_VOLUME_RELATIVE,
        {"volume_step": {"value": volume_change_int}},
    )
    await hass.async_block_till_done()

    assert response.response_type == intent.IntentResponseType.ACTION_DONE
    playing_expected_volume += volume_change_int / 100
    assert math.isclose(idle_entity.volume_level, idle_expected_volume)
    assert math.isclose(playing_entity.volume_level, playing_expected_volume)

    # Test error in method
    with (
        patch.object(
            playing_entity, "async_volume_up", side_effect=RuntimeError("boom!")
        ),
        pytest.raises(intent.IntentError),
    ):
        await intent.async_handle(
            hass,
            "test",
            media_player_intent.INTENT_SET_VOLUME_RELATIVE,
            {"volume_step": {"value": "up"}},
        )

    # Multiple idle media players should not match
    hass.states.async_set(
        playing_entity.entity_id,
        STATE_IDLE,
        attributes={ATTR_SUPPORTED_FEATURES: MediaPlayerEntityFeature.VOLUME_SET},
    )

    with pytest.raises(intent.MatchFailedError):
        await intent.async_handle(
            hass,
            "test",
            media_player_intent.INTENT_SET_VOLUME_RELATIVE,
            {"volume_step": {"value": direction}},
        )

    # Test feature not supported
    for entity_id in (idle_entity.entity_id, playing_entity.entity_id):
        hass.states.async_set(
            entity_id,
            STATE_PLAYING,
            attributes={ATTR_SUPPORTED_FEATURES: MediaPlayerEntityFeature(0)},
        )

    with pytest.raises(intent.MatchFailedError):
        await intent.async_handle(
            hass,
            "test",
            media_player_intent.INTENT_SET_VOLUME_RELATIVE,
            {"volume_step": {"value": direction}},
        )