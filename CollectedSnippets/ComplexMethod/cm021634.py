async def test_media_attributes_are_loaded(
    hass: HomeAssistant, patch_load_json_object: MagicMock
) -> None:
    """Test that media attributes are loaded."""
    mock_entity_id = await setup_mock_component(hass)
    patch_load_json_object.return_value = {MOCK_TITLE_ID: MOCK_GAMES_DATA_LOCKED}

    with patch(
        "homeassistant.components.ps4.media_player.pyps4.Ps4Async.async_get_ps_store_data",
        return_value=None,
    ) as mock_fetch:
        await mock_ddp_response(hass, MOCK_STATUS_PLAYING)

    mock_state = hass.states.get(mock_entity_id)
    mock_attrs = dict(mock_state.attributes)

    # Ensure that data is not fetched.
    assert not mock_fetch.mock_calls

    assert mock_state.state == STATE_PLAYING

    assert len(mock_attrs.get(ATTR_INPUT_SOURCE_LIST)) == 1
    assert mock_attrs.get(ATTR_INPUT_SOURCE_LIST)[0] == MOCK_TITLE_NAME
    assert mock_attrs.get(ATTR_MEDIA_CONTENT_ID) == MOCK_TITLE_ID
    assert mock_attrs.get(ATTR_MEDIA_TITLE) == MOCK_TITLE_NAME
    assert mock_attrs.get(ATTR_MEDIA_CONTENT_TYPE) == MOCK_TITLE_TYPE