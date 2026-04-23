async def test_search_and_play_media_player_intent(hass: HomeAssistant) -> None:
    """Test HassMediaSearchAndPlay intent for media players."""
    await media_player_intent.async_setup_intents(hass)

    entity_id = f"{DOMAIN}.test_media_player"
    attributes = {
        ATTR_SUPPORTED_FEATURES: MediaPlayerEntityFeature.SEARCH_MEDIA
        | MediaPlayerEntityFeature.PLAY_MEDIA
    }
    hass.states.async_set(entity_id, STATE_IDLE, attributes=attributes)

    # Test successful search and play
    search_result_item = BrowseMedia(
        title="Test Track",
        media_class=MediaClass.MUSIC,
        media_content_type=MediaType.MUSIC,
        media_content_id="library/artist/123/album/456/track/789",
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
        {"search_query": {"value": "test query"}},
    )
    await hass.async_block_till_done()

    assert response.response_type == intent.IntentResponseType.ACTION_DONE

    # Response should contain a "media" slot with the matched item.
    assert not response.speech
    media = response.speech_slots.get("media")
    assert media["title"] == "Test Track"

    assert len(search_calls) == 1
    search_call = search_calls[0]
    assert search_call.domain == DOMAIN
    assert search_call.service == SERVICE_SEARCH_MEDIA
    assert search_call.data == {
        "entity_id": entity_id,
        "search_query": "test query",
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

    # Test no search results
    search_results.clear()
    response = await intent.async_handle(
        hass,
        "test",
        media_player_intent.INTENT_MEDIA_SEARCH_AND_PLAY,
        {"search_query": {"value": "another query"}},
    )
    await hass.async_block_till_done()

    assert response.response_type == intent.IntentResponseType.ACTION_DONE

    # A search failure is indicated by no "media" slot in the response.
    assert not response.speech
    assert "media" not in response.speech_slots
    assert len(search_calls) == 2  # Search was called again
    assert len(play_calls) == 1  # Play was not called again

    # Test feature not supported
    hass.states.async_set(
        entity_id,
        STATE_IDLE,
        attributes={},
    )
    with pytest.raises(intent.MatchFailedError):
        await intent.async_handle(
            hass,
            "test",
            media_player_intent.INTENT_MEDIA_SEARCH_AND_PLAY,
            {"search_query": {"value": "test query"}},
        )

    # Test feature not supported (missing SEARCH_MEDIA)
    hass.states.async_set(
        entity_id,
        STATE_IDLE,
        attributes={ATTR_SUPPORTED_FEATURES: MediaPlayerEntityFeature.PLAY_MEDIA},
    )
    with pytest.raises(intent.MatchFailedError):
        await intent.async_handle(
            hass,
            "test",
            media_player_intent.INTENT_MEDIA_SEARCH_AND_PLAY,
            {"search_query": {"value": "test query"}},
        )

    # Test play media service errors
    search_results.append(search_result_item)
    hass.states.async_set(
        entity_id,
        STATE_IDLE,
        attributes={ATTR_SUPPORTED_FEATURES: MediaPlayerEntityFeature.SEARCH_MEDIA},
    )

    async_mock_service(
        hass,
        DOMAIN,
        SERVICE_PLAY_MEDIA,
        raise_exception=HomeAssistantError("Play failed"),
    )
    with pytest.raises(intent.MatchFailedError):
        await intent.async_handle(
            hass,
            "test",
            media_player_intent.INTENT_MEDIA_SEARCH_AND_PLAY,
            {"search_query": {"value": "play error query"}},
        )

    # Test search service error
    hass.states.async_set(entity_id, STATE_IDLE, attributes=attributes)
    async_mock_service(
        hass,
        DOMAIN,
        SERVICE_SEARCH_MEDIA,
        raise_exception=HomeAssistantError("Search failed"),
    )
    with pytest.raises(intent.IntentHandleError, match="Error searching media"):
        await intent.async_handle(
            hass,
            "test",
            media_player_intent.INTENT_MEDIA_SEARCH_AND_PLAY,
            {"search_query": {"value": "error query"}},
        )