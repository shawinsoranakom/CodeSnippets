async def test_browsing_hls(hass: HomeAssistant) -> None:
    """Test browsing HLS camera media source."""
    item = await media_source.async_browse_media(hass, "media-source://camera")
    assert item is not None
    assert item.title == "Camera"
    assert len(item.children) == 0
    assert item.not_shown == 3

    # Adding stream enables HLS camera
    hass.config.components.add("stream")

    item = await media_source.async_browse_media(hass, "media-source://camera")
    assert item.not_shown == 0
    assert len(item.children) == 3
    assert item.children[0].media_content_type == FORMAT_CONTENT_TYPE["hls"]