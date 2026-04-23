async def test_attributes_app_media_paused(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_roku: MagicMock,
) -> None:
    """Test attributes for app with paused media."""
    state = hass.states.get(MAIN_ENTITY_ID)
    assert state
    assert state.state == STATE_PAUSED

    assert state.attributes.get(ATTR_MEDIA_CONTENT_TYPE) == MediaType.APP
    assert state.attributes.get(ATTR_MEDIA_DURATION) == 6496
    assert state.attributes.get(ATTR_MEDIA_POSITION) == 313
    assert state.attributes.get(ATTR_APP_ID) == "74519"
    assert state.attributes.get(ATTR_APP_NAME) == "Pluto TV - It's Free TV"
    assert state.attributes.get(ATTR_INPUT_SOURCE) == "Pluto TV - It's Free TV"