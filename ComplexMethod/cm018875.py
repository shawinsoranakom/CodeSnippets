async def test_async_browse_media(hass: HomeAssistant) -> None:
    """Test browse media."""
    assert await async_setup_component(hass, media_source.DOMAIN, {})
    await hass.async_block_till_done()

    # Test non-media ignored (/media has test.mp3 and not_media.txt)
    media = await media_source.async_browse_media(hass, "")
    assert isinstance(media, media_source.models.BrowseMediaSource)
    assert media.title == "media"
    assert len(media.children) == 2

    # Test content filter
    media = await media_source.async_browse_media(
        hass,
        "",
        content_filter=lambda item: item.media_content_type.startswith("video/"),
    )
    assert isinstance(media, media_source.models.BrowseMediaSource)
    assert media.title == "media"
    assert len(media.children) == 1, media.children
    media.children[0].title = "Epic Sax Guy 10 Hours"
    assert media.not_shown == 1

    # Test content filter adds to original not_shown
    orig_browse = models.MediaSourceItem.async_browse

    async def not_shown_browse(self):
        """Patch browsed item to set not_shown base value."""
        item = await orig_browse(self)
        item.not_shown = 10
        return item

    with patch(
        "homeassistant.components.media_source.models.MediaSourceItem.async_browse",
        not_shown_browse,
    ):
        media = await media_source.async_browse_media(
            hass,
            "",
            content_filter=lambda item: item.media_content_type.startswith("video/"),
        )
    assert isinstance(media, media_source.models.BrowseMediaSource)
    assert media.title == "media"
    assert len(media.children) == 1, media.children
    media.children[0].title = "Epic Sax Guy 10 Hours"
    assert media.not_shown == 11

    # Test invalid media content
    with pytest.raises(BrowseError):
        await media_source.async_browse_media(hass, "invalid")

    # Test base URI returns all domains
    media = await media_source.async_browse_media(hass, const.URI_SCHEME)
    assert isinstance(media, media_source.models.BrowseMediaSource)
    assert len(media.children) == 1
    assert media.children[0].title == "My media"