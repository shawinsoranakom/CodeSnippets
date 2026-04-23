async def test_media_player(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    init_integration: MockConfigEntry,
    mock_jellyfin: MagicMock,
    mock_api: MagicMock,
) -> None:
    """Test the Jellyfin media player."""
    state = hass.states.get("media_player.jellyfin_device")

    assert state
    assert state.state == MediaPlayerState.PAUSED
    assert state.attributes.get(ATTR_DEVICE_CLASS) is None
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == "JELLYFIN-DEVICE"
    assert state.attributes.get(ATTR_ICON) is None
    assert state.attributes.get(ATTR_MEDIA_VOLUME_LEVEL) == 0.0
    assert state.attributes.get(ATTR_MEDIA_VOLUME_MUTED) is True
    assert state.attributes.get(ATTR_MEDIA_DURATION) == 60
    assert state.attributes.get(ATTR_MEDIA_POSITION) == 10
    assert state.attributes.get(ATTR_MEDIA_POSITION_UPDATED_AT)
    assert state.attributes.get(ATTR_MEDIA_CONTENT_ID) == "EPISODE-UUID"
    assert state.attributes.get(ATTR_MEDIA_CONTENT_TYPE) == MediaType.TVSHOW
    assert state.attributes.get(ATTR_MEDIA_SERIES_TITLE) == "SERIES"
    assert state.attributes.get(ATTR_MEDIA_SEASON) == 1
    assert state.attributes.get(ATTR_MEDIA_EPISODE) == 3

    entry = entity_registry.async_get(state.entity_id)
    assert entry
    assert entry.device_id
    assert entry.entity_category is None
    assert entry.unique_id == "SERVER-UUID-SESSION-UUID"

    assert len(mock_api.sessions.mock_calls) == 1
    async_fire_time_changed(hass, utcnow() + timedelta(seconds=10))
    await hass.async_block_till_done()
    assert len(mock_api.sessions.mock_calls) == 2

    mock_api.sessions.return_value = []
    async_fire_time_changed(hass, utcnow() + timedelta(seconds=20))
    await hass.async_block_till_done()
    assert len(mock_api.sessions.mock_calls) == 3

    device = device_registry.async_get(entry.device_id)
    assert device
    assert device.configuration_url is None
    assert device.connections == set()
    assert device.entry_type is None
    assert device.hw_version is None
    assert device.identifiers == {(DOMAIN, "DEVICE-UUID")}
    assert device.manufacturer == "Jellyfin"
    assert device.name == "JELLYFIN-DEVICE"
    assert device.sw_version == "1.0.0"