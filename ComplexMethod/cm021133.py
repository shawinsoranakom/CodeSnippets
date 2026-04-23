async def test_browse_media_time_timezone(
    hass: HomeAssistant,
    ufp: MockUFPFixture,
    doorbell: Camera,
    start: datetime,
    months: int,
) -> None:
    """Test browsing time selector level media."""

    end = datetime.fromisoformat("2022-08-31 21:00:00-07:00")
    end_local = dt_util.as_local(end)

    ufp.api.bootstrap._recording_start = dt_util.as_utc(start)

    ufp.api.get_bootstrap = AsyncMock(return_value=ufp.api.bootstrap)
    await init_entry(hass, ufp, [doorbell], regenerate_ids=False)

    base_id = f"test_id:browse:{doorbell.id}:all"
    source = await async_get_media_source(hass)
    media_item = MediaSourceItem(hass, DOMAIN, base_id, None)

    browse = await source.async_browse_media(media_item)

    assert browse.title == f"UnifiProtect > {doorbell.name} > All Events"
    assert browse.identifier == base_id
    assert len(browse.children) == 3 + months
    assert browse.children[0].title == "Last 24 Hours"
    assert browse.children[0].identifier == f"{base_id}:recent:1"
    assert browse.children[1].title == "Last 7 Days"
    assert browse.children[1].identifier == f"{base_id}:recent:7"
    assert browse.children[2].title == "Last 30 Days"
    assert browse.children[2].identifier == f"{base_id}:recent:30"
    assert browse.children[3].title == f"{end_local.strftime('%B %Y')}"
    assert (
        browse.children[3].identifier
        == f"{base_id}:range:{end_local.year}:{end_local.month}"
    )