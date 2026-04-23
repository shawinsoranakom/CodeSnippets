async def test_browse_media_as_dict() -> None:
    """Test BrowseMediaSource conversion to media player item dict."""
    base = models.BrowseMediaSource(
        domain=const.DOMAIN,
        identifier="media",
        media_class=MediaClass.DIRECTORY,
        media_content_type="folder",
        title="media/",
        can_play=False,
        can_expand=True,
        children_media_class=MediaClass.MUSIC,
    )
    base.children = [
        models.BrowseMediaSource(
            domain=const.DOMAIN,
            identifier="media/test.mp3",
            media_class=MediaClass.MUSIC,
            media_content_type=MediaType.MUSIC,
            title="test.mp3",
            can_play=True,
            can_expand=False,
        )
    ]

    item = base.as_dict()
    assert item["title"] == "media/"
    assert item["media_class"] == MediaClass.DIRECTORY
    assert item["media_content_type"] == "folder"
    assert item["media_content_id"] == f"{const.URI_SCHEME}{const.DOMAIN}/media"
    assert not item["can_play"]
    assert item["can_expand"]
    assert item["children_media_class"] == MediaClass.MUSIC
    assert len(item["children"]) == 1
    assert item["children"][0]["title"] == "test.mp3"
    assert item["children"][0]["media_class"] == MediaClass.MUSIC