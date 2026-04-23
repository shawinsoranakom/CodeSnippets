async def test_browse_media_get_root(
    hass: HomeAssistant,
    mock_immich: Mock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test browse_media returning root media sources."""
    assert await async_setup_component(hass, "media_source", {})

    with patch("homeassistant.components.immich.PLATFORMS", []):
        await setup_integration(hass, mock_config_entry)

    source = await async_get_media_source(hass)

    # get root
    item = MediaSourceItem(hass, DOMAIN, "", None)
    result = await source.async_browse_media(item)

    assert result
    assert len(result.children) == 1
    media_file = result.children[0]
    assert isinstance(media_file, BrowseMedia)
    assert media_file.title == "Someone"
    assert media_file.media_content_id == (
        "media-source://immich/e7ef5713-9dab-4bd4-b899-715b0ca4379e"
    )

    # get collections
    item = MediaSourceItem(hass, DOMAIN, "e7ef5713-9dab-4bd4-b899-715b0ca4379e", None)
    result = await source.async_browse_media(item)

    assert result
    assert len(result.children) == 4

    media_file = result.children[0]
    assert isinstance(media_file, BrowseMedia)
    assert media_file.title == "albums"
    assert media_file.media_content_id == (
        "media-source://immich/e7ef5713-9dab-4bd4-b899-715b0ca4379e|albums"
    )

    media_file = result.children[1]
    assert isinstance(media_file, BrowseMedia)
    assert media_file.title == "favorites"
    assert media_file.media_content_id == (
        "media-source://immich/e7ef5713-9dab-4bd4-b899-715b0ca4379e|favorites|favorites"
    )

    media_file = result.children[2]
    assert isinstance(media_file, BrowseMedia)
    assert media_file.title == "people"
    assert media_file.media_content_id == (
        "media-source://immich/e7ef5713-9dab-4bd4-b899-715b0ca4379e|people"
    )

    media_file = result.children[3]
    assert isinstance(media_file, BrowseMedia)
    assert media_file.title == "tags"
    assert media_file.media_content_id == (
        "media-source://immich/e7ef5713-9dab-4bd4-b899-715b0ca4379e|tags"
    )