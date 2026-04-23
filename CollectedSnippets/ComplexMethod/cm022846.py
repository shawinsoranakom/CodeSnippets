async def test_root_object(hass: HomeAssistant) -> None:
    """Test getting a root object."""
    assert (
        await lovelace_cast.async_get_media_browser_root_object(hass, "some-type") == []
    )

    root = await lovelace_cast.async_get_media_browser_root_object(
        hass, lovelace_cast.CAST_TYPE_CHROMECAST
    )
    assert len(root) == 1
    item = root[0]
    assert item.title == "Dashboards"
    assert item.media_class == MediaClass.APP
    assert item.media_content_id == ""
    assert item.media_content_type == lovelace_cast.DOMAIN
    assert item.thumbnail == "/api/brands/integration/lovelace/logo.png"
    assert item.can_play is False
    assert item.can_expand is True