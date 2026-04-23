async def test_browse_media_parent_no_children() -> None:
    """Test BrowseMediaSource conversion to media player item dict."""
    base = models.BrowseMediaSource(
        domain=const.DOMAIN,
        identifier="media",
        media_class=MediaClass.DIRECTORY,
        media_content_type="folder",
        title="media/",
        can_play=False,
        can_expand=True,
    )

    item = base.as_dict()
    assert item["title"] == "media/"
    assert item["media_class"] == MediaClass.DIRECTORY
    assert item["media_content_type"] == "folder"
    assert item["media_content_id"] == f"{const.URI_SCHEME}{const.DOMAIN}/media"
    assert not item["can_play"]
    assert item["can_expand"]
    assert len(item["children"]) == 0
    assert item["children_media_class"] is None