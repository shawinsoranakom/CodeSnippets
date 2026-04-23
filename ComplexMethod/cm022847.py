async def test_browse_media(hass: HomeAssistant) -> None:
    """Test browse media."""
    top_level_items = await lovelace_cast.async_browse_media(
        hass, "lovelace", "", lovelace_cast.CAST_TYPE_CHROMECAST
    )

    assert len(top_level_items.children) == 2

    child_1 = top_level_items.children[0]
    assert child_1.title == "Default"
    assert child_1.media_class == MediaClass.APP
    assert child_1.media_content_id == lovelace_cast.DEFAULT_DASHBOARD
    assert child_1.media_content_type == lovelace_cast.DOMAIN
    assert child_1.thumbnail == "/api/brands/integration/lovelace/logo.png"
    assert child_1.can_play is True
    assert child_1.can_expand is False

    child_2 = top_level_items.children[1]
    assert child_2.title == "YAML Title"
    assert child_2.media_class == MediaClass.APP
    assert child_2.media_content_id == "yaml-with-views"
    assert child_2.media_content_type == lovelace_cast.DOMAIN
    assert child_2.thumbnail == "/api/brands/integration/lovelace/logo.png"
    assert child_2.can_play is True
    assert child_2.can_expand is True

    child_2 = await lovelace_cast.async_browse_media(
        hass, "lovelace", child_2.media_content_id, lovelace_cast.CAST_TYPE_CHROMECAST
    )

    assert len(child_2.children) == 2

    grandchild_1 = child_2.children[0]
    assert grandchild_1.title == "Hello"
    assert grandchild_1.media_class == MediaClass.APP
    assert grandchild_1.media_content_id == "yaml-with-views/0"
    assert grandchild_1.media_content_type == lovelace_cast.DOMAIN
    assert grandchild_1.thumbnail == "/api/brands/integration/lovelace/logo.png"
    assert grandchild_1.can_play is True
    assert grandchild_1.can_expand is False

    grandchild_2 = child_2.children[1]
    assert grandchild_2.title == "second-view"
    assert grandchild_2.media_class == MediaClass.APP
    assert grandchild_2.media_content_id == "yaml-with-views/second-view"
    assert grandchild_2.media_content_type == lovelace_cast.DOMAIN
    assert grandchild_2.thumbnail == "/api/brands/integration/lovelace/logo.png"
    assert grandchild_2.can_play is True
    assert grandchild_2.can_expand is False

    with pytest.raises(HomeAssistantError):
        await lovelace_cast.async_browse_media(
            hass,
            "lovelace",
            "non-existing-dashboard",
            lovelace_cast.CAST_TYPE_CHROMECAST,
        )