async def test_media_player_setup(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    ufp: MockUFPFixture,
    doorbell: Camera,
    unadopted_camera: Camera,
) -> None:
    """Test media_player entity setup."""

    await init_entry(hass, ufp, [doorbell, unadopted_camera])
    assert_entity_counts(hass, Platform.MEDIA_PLAYER, 1, 1)

    unique_id = f"{doorbell.mac}_speaker"
    entity_id = "media_player.test_camera_speaker"

    entity = entity_registry.async_get(entity_id)
    assert entity
    assert entity.unique_id == unique_id

    expected_volume = float(doorbell.speaker_settings.speaker_volume / 100)

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_IDLE
    assert state.attributes[ATTR_ATTRIBUTION] == DEFAULT_ATTRIBUTION
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 136708
    assert state.attributes[ATTR_MEDIA_CONTENT_TYPE] == "music"
    assert state.attributes[ATTR_MEDIA_VOLUME_LEVEL] == expected_volume