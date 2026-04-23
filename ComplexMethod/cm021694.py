async def test_search_media(
    hass: HomeAssistant,
    music_assistant_client: MagicMock,
    search_query: str,
    media_content_type: str,
    expected_items: int,
) -> None:
    """Test the async_search_media method with different content types."""
    await setup_integration_from_fixtures(hass, music_assistant_client)

    # Create mock search results
    media_types = []
    if media_content_type == MediaType.TRACK:
        media_types = ["track"]
    elif media_content_type == MediaType.ALBUM:
        media_types = ["album"]
    elif media_content_type == MediaType.ARTIST:
        media_types = ["artist"]
    elif media_content_type == MediaType.PLAYLIST:
        media_types = ["playlist"]
    elif media_content_type == MEDIA_TYPE_RADIO:
        media_types = ["radio"]
    elif media_content_type == MediaType.PODCAST:
        media_types = ["podcast"]
    elif media_content_type == MEDIA_TYPE_AUDIOBOOK:
        media_types = ["audiobook"]
    elif media_content_type is None:
        media_types = [
            "artist",
            "album",
            "track",
            "playlist",
            "radio",
            "podcast",
            "audiobook",
        ]

    mock_results = MockSearchResults(media_types)

    # Use patch instead of trying to mock return_value
    with patch.object(
        music_assistant_client.music, "search", return_value=mock_results
    ):
        # Create search query
        query = SearchMediaQuery(
            search_query=search_query,
            media_content_type=media_content_type,
        )

        # Perform search
        search_results = await async_search_media(music_assistant_client, query)

        # Verify search results
        assert isinstance(search_results, SearchMedia)

        if media_content_type is not None:
            # For specific media types, expect up to 5 results
            assert len(search_results.result) <= 5
        else:
            # For "all types" search, we'd expect items from each type
            # But since we're returning exactly 5 items per type (from mock)
            # we'd expect 5 * 7 = 35 items maximum
            assert len(search_results.result) <= 35