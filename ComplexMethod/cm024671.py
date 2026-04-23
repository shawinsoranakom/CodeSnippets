async def test_browse_albums(
    hass: HomeAssistant,
    album_path: str,
    expected_album_title: str,
    expected_results: list[tuple[str, str]],
    expected_medias: list[tuple[str, str]],
) -> None:
    """Test a media source with no eligible camera devices."""
    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}")
    assert browse.domain == DOMAIN
    assert browse.identifier is None
    assert browse.title == "Google Photos"
    assert [(child.identifier, child.title) for child in browse.children] == [
        (CONFIG_ENTRY_ID, "Account Name")
    ]

    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}/{CONFIG_ENTRY_ID}")
    assert browse.domain == DOMAIN
    assert browse.identifier == CONFIG_ENTRY_ID
    assert browse.title == "Account Name"
    assert [(child.identifier, child.title) for child in browse.children] == [
        (f"{CONFIG_ENTRY_ID}/a/album-media-id-1", "Album title"),
    ]

    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}/{album_path}")
    assert browse.domain == DOMAIN
    assert browse.identifier == album_path
    assert browse.title == "Account Name"
    assert [
        (child.identifier, child.title) for child in browse.children
    ] == expected_results

    media = [
        await async_resolve_media(
            hass, f"{URI_SCHEME}{DOMAIN}/{child.identifier}", None
        )
        for child in browse.children
    ]
    assert [
        (play_media.url, play_media.mime_type) for play_media in media
    ] == expected_medias