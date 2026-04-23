async def test_movie_library(
    hass: HomeAssistant,
    mock_client: MagicMock,
    init_integration: MockConfigEntry,
    mock_jellyfin: MagicMock,
    mock_api: MagicMock,
    snapshot: SnapshotAssertion,
) -> None:
    """Test browsing a Jellyfin Movie Library."""

    # Test empty movie library
    mock_api.get_item.side_effect = None
    mock_api.get_item.return_value = load_json_fixture("movie-collection.json")
    mock_api.user_items.side_effect = None
    mock_api.user_items.return_value = {"Items": []}

    browse = await async_browse_media(
        hass, f"{URI_SCHEME}{DOMAIN}/MOVIE-COLLECTION-FOLDER-UUID"
    )

    assert browse.domain == DOMAIN
    assert browse.identifier == "MOVIE-COLLECTION-FOLDER-UUID"
    assert browse.title == "Movies"
    assert browse.children == []

    # Test browsing a movie library containing movies
    mock_api.user_items.side_effect = None
    mock_api.user_items.return_value = load_json_fixture("movies.json")

    browse = await async_browse_media(
        hass, f"{URI_SCHEME}{DOMAIN}/MOVIE-COLLECTION-FOLDER-UUID"
    )

    assert browse.domain == DOMAIN
    assert browse.identifier == "MOVIE-COLLECTION-FOLDER-UUID"
    assert browse.title == "Movies"
    assert vars(browse.children[0]) == snapshot