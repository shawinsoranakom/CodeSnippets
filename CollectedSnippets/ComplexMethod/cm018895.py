def test_master_state(hass: HomeAssistant) -> None:
    """Test master state attributes."""
    state = hass.states.get(TEST_MASTER_ENTITY_NAME)
    assert state.state == STATE_PAUSED
    assert state.attributes[ATTR_FRIENDLY_NAME] == "OwnTone server"
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == SUPPORTED_FEATURES
    assert not state.attributes[ATTR_MEDIA_VOLUME_MUTED]
    assert state.attributes[ATTR_MEDIA_VOLUME_LEVEL] == 0.2
    assert state.attributes[ATTR_MEDIA_CONTENT_ID] == 12322
    assert state.attributes[ATTR_MEDIA_CONTENT_TYPE] == MediaType.MUSIC
    assert state.attributes[ATTR_MEDIA_DURATION] == 0.05
    assert state.attributes[ATTR_MEDIA_POSITION] == 0.005
    assert state.attributes[ATTR_MEDIA_TITLE] == "No album"  # reversed for url
    assert state.attributes[ATTR_MEDIA_ARTIST] == "Some artist"
    assert state.attributes[ATTR_MEDIA_ALBUM_NAME] == "Some song"  # reversed
    assert state.attributes[ATTR_MEDIA_ALBUM_ARTIST] == "The xx"
    assert state.attributes[ATTR_MEDIA_TRACK] == 1
    assert not state.attributes[ATTR_MEDIA_SHUFFLE]