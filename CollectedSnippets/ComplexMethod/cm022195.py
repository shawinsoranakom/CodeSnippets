async def test_browse_media_object(hass: HomeAssistant, dms_device_mock: Mock) -> None:
    """Test async_browse_object via async_browse_media."""
    object_id = "1234"
    child_titles = ("Item 1", "Thing", "Item 2")
    dms_device_mock.async_browse_metadata.return_value = didl_lite.Container(
        id=object_id, restricted="false", title="subcontainer"
    )
    children_result = DmsDevice.BrowseResult([], 3, 3, 0)
    for title in child_titles:
        children_result.result.append(
            didl_lite.Item(
                id=title + "_id",
                restricted="false",
                title=title,
                res=[
                    didl_lite.Resource(
                        uri=title + "_url", protocol_info="http-get:*:audio/mpeg:"
                    )
                ],
            ),
        )
    dms_device_mock.async_browse_direct_children.return_value = children_result

    result = await async_browse_media(hass, f":{object_id}")
    dms_device_mock.async_browse_metadata.assert_awaited_once_with(
        object_id, metadata_filter=ANY
    )
    dms_device_mock.async_browse_direct_children.assert_awaited_once_with(
        object_id, metadata_filter=ANY, sort_criteria=ANY
    )

    assert result.domain == DOMAIN
    assert result.identifier == f"{MOCK_SOURCE_ID}/:{object_id}"
    assert result.title == "subcontainer"
    assert not result.can_play
    assert result.can_expand
    assert result.children
    for child, title in zip(result.children, child_titles, strict=False):
        assert isinstance(child, BrowseMediaSource)
        assert child.identifier == f"{MOCK_SOURCE_ID}/:{title}_id"
        assert child.title == title
        assert child.can_play
        assert not child.can_expand
        assert not child.children