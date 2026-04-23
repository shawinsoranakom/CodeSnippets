async def test_media_attributes_are_fetched(hass: HomeAssistant) -> None:
    """Test that media attributes are fetched."""
    mock_entity_id = await setup_mock_component(hass)
    mock_func = "homeassistant.components.ps4.media_player.pyps4.Ps4Async.async_get_ps_store_data"

    # Mock result from fetching data.
    mock_result = MagicMock()
    mock_result.name = MOCK_TITLE_NAME
    mock_result.cover_art = MOCK_TITLE_ART_URL
    mock_result.game_type = "not_an_app"

    with patch(mock_func, return_value=mock_result) as mock_fetch:
        await mock_ddp_response(hass, MOCK_STATUS_PLAYING)
        await hass.async_block_till_done(wait_background_tasks=True)

    mock_state = hass.states.get(mock_entity_id)
    mock_attrs = dict(mock_state.attributes)

    assert len(mock_fetch.mock_calls) == 1

    assert mock_state.state == STATE_PLAYING
    assert len(mock_attrs.get(ATTR_INPUT_SOURCE_LIST)) == 1
    assert mock_attrs.get(ATTR_INPUT_SOURCE_LIST)[0] == MOCK_TITLE_NAME
    assert mock_attrs.get(ATTR_MEDIA_CONTENT_ID) == MOCK_TITLE_ID
    assert mock_attrs.get(ATTR_MEDIA_TITLE) == MOCK_TITLE_NAME
    assert mock_attrs.get(ATTR_MEDIA_CONTENT_TYPE) == MOCK_TITLE_TYPE

    # Change state so that the next fetch is called.
    await mock_ddp_response(hass, MOCK_STATUS_STANDBY)

    # Test that content type of app is set.
    mock_result.game_type = PS_TYPE_APP

    with patch(mock_func, return_value=mock_result) as mock_fetch_app:
        await mock_ddp_response(hass, MOCK_STATUS_PLAYING)
        await hass.async_block_till_done(wait_background_tasks=True)

    mock_state = hass.states.get(mock_entity_id)
    mock_attrs = dict(mock_state.attributes)

    assert len(mock_fetch_app.mock_calls) == 1
    assert mock_attrs.get(ATTR_MEDIA_CONTENT_TYPE) == MediaType.APP