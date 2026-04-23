async def test_media_player_music(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    init_integration: MockConfigEntry,
    mock_jellyfin: MagicMock,
    mock_api: MagicMock,
) -> None:
    """Test the Jellyfin media player."""
    state = hass.states.get("media_player.jellyfin_device_four")

    assert state
    assert state.state == MediaPlayerState.PLAYING
    assert state.attributes.get(ATTR_DEVICE_CLASS) is None
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == "JELLYFIN DEVICE FOUR"
    assert state.attributes.get(ATTR_ICON) is None
    assert state.attributes.get(ATTR_MEDIA_VOLUME_LEVEL) == 1.0
    assert state.attributes.get(ATTR_MEDIA_VOLUME_MUTED) is False
    assert state.attributes.get(ATTR_MEDIA_DURATION) == 73
    assert state.attributes.get(ATTR_MEDIA_POSITION) == 22
    assert state.attributes.get(ATTR_MEDIA_POSITION_UPDATED_AT)
    assert state.attributes.get(ATTR_MEDIA_CONTENT_ID) == "MUSIC-UUID"
    assert state.attributes.get(ATTR_MEDIA_CONTENT_TYPE) == MediaType.MUSIC
    assert state.attributes.get(ATTR_MEDIA_ALBUM_NAME) == "ALBUM"
    assert state.attributes.get(ATTR_MEDIA_ALBUM_ARTIST) == "Album Artist"
    assert state.attributes.get(ATTR_MEDIA_ARTIST) == "Contributing Artist"
    assert state.attributes.get(ATTR_MEDIA_TRACK) == 1
    assert state.attributes.get(ATTR_MEDIA_SERIES_TITLE) is None
    assert state.attributes.get(ATTR_MEDIA_SEASON) is None
    assert state.attributes.get(ATTR_MEDIA_EPISODE) is None
    entity_picture = state.attributes.get(ATTR_ENTITY_PICTURE)
    assert entity_picture is not None
    assert entity_picture.startswith(
        "/api/media_player_proxy/media_player.jellyfin_device_four?token="
    )
    assert "cache=7f15194cd71877c7" in entity_picture

    entry = entity_registry.async_get(state.entity_id)
    assert entry
    assert entry.device_id is None
    assert entry.entity_category is None
    assert entry.unique_id == "SERVER-UUID-SESSION-UUID-FOUR"