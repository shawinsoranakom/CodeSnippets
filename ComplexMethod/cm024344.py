async def test_browsing(hass: HomeAssistant, setup: str) -> None:
    """Test browsing TTS media source."""
    item = await media_source.async_browse_media(hass, "media-source://tts")

    assert item is not None
    assert item.title == "Text-to-speech"
    assert item.children is not None
    assert len(item.children) == 1
    assert item.can_play is False
    assert item.can_expand is True

    item_child = await media_source.async_browse_media(
        hass, item.children[0].media_content_id
    )

    assert item_child is not None
    assert item_child.media_content_id == item.children[0].media_content_id
    assert item_child.title == "Test"
    assert item_child.children is None
    assert item_child.can_play is False
    assert item_child.can_expand is True
    assert item_child.thumbnail == "/api/brands/integration/test/logo.png"

    item_child = await media_source.async_browse_media(
        hass, item.children[0].media_content_id + "?message=bla"
    )

    assert item_child is not None
    assert (
        item_child.media_content_id
        == item.children[0].media_content_id + "?message=bla"
    )
    assert item_child.title == "Test"
    assert item_child.children is None
    assert item_child.can_play is False
    assert item_child.can_expand is True

    with pytest.raises(BrowseError):
        await media_source.async_browse_media(hass, "media-source://tts/non-existing")