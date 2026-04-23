async def test_browse_media_event_type(
    hass: HomeAssistant, ufp: MockUFPFixture, doorbell: Camera
) -> None:
    """Test browsing event type selector level media."""

    ufp.api.get_bootstrap = AsyncMock(return_value=ufp.api.bootstrap)
    await init_entry(hass, ufp, [doorbell], regenerate_ids=False)

    source = await async_get_media_source(hass)
    media_item = MediaSourceItem(hass, DOMAIN, "test_id:browse:all", None)

    browse = await source.async_browse_media(media_item)

    assert browse.title == "UnifiProtect > All Cameras"
    assert browse.identifier == "test_id:browse:all"
    assert len(browse.children) == 5
    assert browse.children[0].title == "All Events"
    assert browse.children[0].identifier == "test_id:browse:all:all"
    assert browse.children[1].title == "Ring Events"
    assert browse.children[1].identifier == "test_id:browse:all:ring"
    assert browse.children[2].title == "Motion Events"
    assert browse.children[2].identifier == "test_id:browse:all:motion"
    assert browse.children[3].title == "Object Detections"
    assert browse.children[3].identifier == "test_id:browse:all:smart"
    assert browse.children[4].title == "Audio Detections"
    assert browse.children[4].identifier == "test_id:browse:all:audio"