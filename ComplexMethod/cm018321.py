async def test_music_library(
    hass: HomeAssistant,
    mock_client: MagicMock,
    init_integration: MockConfigEntry,
    mock_jellyfin: MagicMock,
    mock_api: MagicMock,
    snapshot: SnapshotAssertion,
) -> None:
    """Test browsing a Jellyfin Music Library."""

    # Test browsinng an empty music library
    mock_api.get_item.side_effect = None
    mock_api.get_item.return_value = load_json_fixture("music-collection.json")
    mock_api.user_items.side_effect = None
    mock_api.user_items.return_value = {"Items": []}

    browse = await async_browse_media(
        hass, f"{URI_SCHEME}{DOMAIN}/MUSIC-COLLECTION-FOLDER-UUID"
    )

    assert browse.domain == DOMAIN
    assert browse.identifier == "MUSIC-COLLECTION-FOLDER-UUID"
    assert browse.title == "Music"
    assert browse.children == []

    # Test browsing a music library containing albums
    mock_api.user_items.side_effect = None
    mock_api.user_items.return_value = load_json_fixture("albums.json")

    browse = await async_browse_media(
        hass, f"{URI_SCHEME}{DOMAIN}/MUSIC-COLLECTION-FOLDER-UUID"
    )

    assert browse.domain == DOMAIN
    assert browse.identifier == "MUSIC-COLLECTION-FOLDER-UUID"
    assert browse.title == "Music"
    assert vars(browse.children[0]) == snapshot

    # Test browsing an artist
    mock_api.get_item.side_effect = None
    mock_api.get_item.return_value = load_json_fixture("artist.json")
    mock_api.user_items.side_effect = None
    mock_api.user_items.return_value = load_json_fixture("albums.json")

    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}/ARTIST-UUID")

    assert browse.domain == DOMAIN
    assert browse.identifier == "ARTIST-UUID"
    assert browse.title == "ARTIST"
    assert vars(browse.children[0]) == snapshot

    # Test browsing an album
    mock_api.get_item.side_effect = None
    mock_api.get_item.return_value = load_json_fixture("album.json")
    mock_api.user_items.side_effect = None
    mock_api.user_items.return_value = load_json_fixture("tracks.json")

    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}/ALBUM-UUID")

    assert browse.domain == DOMAIN
    assert browse.identifier == "ALBUM-UUID"
    assert browse.title == "ALBUM"
    assert vars(browse.children[0]) == snapshot

    # Test browsing an album with a track with no source
    mock_api.user_items.side_effect = None
    mock_api.user_items.return_value = load_json_fixture("tracks-nosource.json")

    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}/ALBUM-UUID")

    assert browse.domain == DOMAIN
    assert browse.identifier == "ALBUM-UUID"
    assert browse.title == "ALBUM"

    assert browse.children == []

    # Test browsing an album with a track with no path
    mock_api.user_items.side_effect = None
    mock_api.user_items.return_value = load_json_fixture("tracks-nopath.json")

    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}/ALBUM-UUID")

    assert browse.domain == DOMAIN
    assert browse.identifier == "ALBUM-UUID"
    assert browse.title == "ALBUM"

    assert browse.children == []

    # Test browsing an album with a track with an unknown file extension
    mock_api.user_items.side_effect = None
    mock_api.user_items.return_value = load_json_fixture(
        "tracks-unknown-extension.json"
    )

    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}/ALBUM-UUID")

    assert browse.domain == DOMAIN
    assert browse.identifier == "ALBUM-UUID"
    assert browse.title == "ALBUM"

    assert browse.children == []