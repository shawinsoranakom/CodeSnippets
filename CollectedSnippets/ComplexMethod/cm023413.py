async def test_tv_attributes(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Test attributes for Roku TV."""
    state = hass.states.get(TV_ENTITY_ID)
    assert state
    assert state.state == STATE_ON

    assert state.attributes.get(ATTR_APP_ID) == "tvinput.dtv"
    assert state.attributes.get(ATTR_APP_NAME) == "Antenna TV"
    assert state.attributes.get(ATTR_INPUT_SOURCE) == "Antenna TV"
    assert state.attributes.get(ATTR_MEDIA_CONTENT_TYPE) == MediaType.CHANNEL
    assert state.attributes.get(ATTR_MEDIA_CHANNEL) == "getTV (14.3)"
    assert state.attributes.get(ATTR_MEDIA_TITLE) == "Airwolf"