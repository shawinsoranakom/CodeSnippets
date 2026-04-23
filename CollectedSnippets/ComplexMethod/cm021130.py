async def test_browse_media_camera_offline(
    hass: HomeAssistant, ufp: MockUFPFixture, doorbell: Camera
) -> None:
    """Test browsing camera selector level media when camera is offline."""

    doorbell.is_connected = False

    ufp.api.get_bootstrap = AsyncMock(return_value=ufp.api.bootstrap)
    await init_entry(hass, ufp, [doorbell])

    source = await async_get_media_source(hass)
    media_item = MediaSourceItem(hass, DOMAIN, "test_id:browse", None)

    browse = await source.async_browse_media(media_item)

    assert browse.title == "UnifiProtect"
    assert browse.identifier == "test_id:browse"
    assert len(browse.children) == 2
    assert browse.children[0].title == "All Cameras"
    assert browse.children[0].identifier == "test_id:browse:all"
    assert browse.children[1].title == doorbell.name
    assert browse.children[1].identifier == f"test_id:browse:{doorbell.id}"
    assert browse.children[1].thumbnail is None