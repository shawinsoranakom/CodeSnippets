async def test_search_and_play_media_player_intent_with_media_class(
    hass: HomeAssistant,
) -> None:
    """Test HassMediaSearchAndPlay intent with media_class parameter."""
    await media_player_intent.async_setup_intents(hass)

    entity_id = f"{DOMAIN}.test_media_player"
    attributes = {
        ATTR_SUPPORTED_FEATURES: MediaPlayerEntityFeature.SEARCH_MEDIA
        | MediaPlayerEntityFeature.PLAY_MEDIA
    }
    hass.states.async_set(entity_id, STATE_IDLE, attributes=attributes)

    # Test successful search and play with media_class filter
    search_result_item = BrowseMedia(
        title="Test Album",
        media_class=MediaClass.ALBUM,
        media_content_type=MediaType.ALBUM,
        media_content_id="library/album/123",
        can_play=True,
        can_expand=False,
    )

    # Mock service calls
    search_results = [search_result_item]
    search_calls = async_mock_service(
        hass,
        DOMAIN,
        SERVICE_SEARCH_MEDIA,
        response={entity_id: SearchMedia(result=search_results)},
    )
    play_calls = async_mock_service(hass, DOMAIN, SERVICE_PLAY_MEDIA)

    response = await intent.async_handle(
        hass,
        "test",
        media_player_intent.INTENT_MEDIA_SEARCH_AND_PLAY,
        {"search_query": {"value": "test album"}, "media_class": {"value": "album"}},
    )
    await hass.async_block_till_done()

    assert response.response_type == intent.IntentResponseType.ACTION_DONE

    # Response should contain a "media" slot with the matched item.
    assert not response.speech
    media = response.speech_slots.get("media")
    assert media["title"] == "Test Album"

    assert len(search_calls) == 1
    search_call = search_calls[0]
    assert search_call.domain == DOMAIN
    assert search_call.service == SERVICE_SEARCH_MEDIA
    assert search_call.data == {
        "entity_id": entity_id,
        "search_query": "test album",
        "media_filter_classes": ["album"],
    }

    assert len(play_calls) == 1
    play_call = play_calls[0]
    assert play_call.domain == DOMAIN
    assert play_call.service == SERVICE_PLAY_MEDIA
    assert play_call.data == {
        "entity_id": entity_id,
        "media_content_id": search_result_item.media_content_id,
        "media_content_type": search_result_item.media_content_type,
    }

    # Test with invalid media_class (should raise validation error)
    with pytest.raises(intent.InvalidSlotInfo):
        await intent.async_handle(
            hass,
            "test",
            media_player_intent.INTENT_MEDIA_SEARCH_AND_PLAY,
            {
                "search_query": {"value": "test query"},
                "media_class": {"value": "invalid_class"},
            },
        )