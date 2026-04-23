async def test_tv_library(
    hass: HomeAssistant,
    mock_client: MagicMock,
    init_integration: MockConfigEntry,
    mock_jellyfin: MagicMock,
    mock_api: MagicMock,
    snapshot: SnapshotAssertion,
) -> None:
    """Test browsing a Jellyfin TV Library."""

    # Test browsing an empty tv library
    mock_api.get_item.side_effect = None
    mock_api.get_item.return_value = load_json_fixture("tv-collection.json")
    mock_api.user_items.side_effect = None
    mock_api.user_items.return_value = {"Items": []}

    browse = await async_browse_media(
        hass, f"{URI_SCHEME}{DOMAIN}/TV-COLLECTION-FOLDER-UUID"
    )

    assert browse.domain == DOMAIN
    assert browse.identifier == "TV-COLLECTION-FOLDER-UUID"
    assert browse.title == "TVShows"
    assert browse.children == []

    # Test browsing a tv library containing series
    mock_api.user_items.side_effect = None
    mock_api.user_items.return_value = load_json_fixture("series-list.json")

    browse = await async_browse_media(
        hass, f"{URI_SCHEME}{DOMAIN}/TV-COLLECTION-FOLDER-UUID"
    )

    assert browse.domain == DOMAIN
    assert browse.identifier == "TV-COLLECTION-FOLDER-UUID"
    assert browse.title == "TVShows"
    assert vars(browse.children[0]) == snapshot

    # Test browsing a series
    mock_api.get_item.side_effect = None
    mock_api.get_item.return_value = load_json_fixture("series.json")
    mock_api.user_items.side_effect = None
    mock_api.user_items.return_value = load_json_fixture("seasons.json")

    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}/SERIES-UUID")

    assert browse.domain == DOMAIN
    assert browse.identifier == "SERIES-UUID"
    assert browse.title == "SERIES"
    assert vars(browse.children[0]) == snapshot

    # Test browsing a season
    mock_api.get_item.side_effect = None
    mock_api.get_item.return_value = load_json_fixture("season.json")
    mock_api.user_items.side_effect = None
    mock_api.user_items.return_value = load_json_fixture("episodes.json")

    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}/SEASON-UUID")

    assert browse.domain == DOMAIN
    assert browse.identifier == "SEASON-UUID"
    assert browse.title == "SEASON"
    assert vars(browse.children[0]) == snapshot