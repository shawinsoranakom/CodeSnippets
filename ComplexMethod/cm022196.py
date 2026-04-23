async def test_browse_media_search(hass: HomeAssistant, dms_device_mock: Mock) -> None:
    """Test async_browse_media with a search query."""
    query = 'dc:title contains "FooBar"'
    object_details = (("111", "FooBar baz"), ("432", "Not FooBar"), ("99", "FooBar"))
    dms_device_mock.async_search_directory.return_value = DmsDevice.BrowseResult(
        [
            didl_lite.DidlObject(id=ob_id, restricted="false", title=title)
            for ob_id, title in object_details
        ],
        3,
        3,
        0,
    )
    # Test that descriptors are skipped
    dms_device_mock.async_search_directory.return_value.result.insert(
        1, didl_lite.Descriptor("id", "name_space")
    )

    result = await async_browse_media(hass, f"?{query}")
    assert result.identifier == f"{MOCK_SOURCE_ID}/?{query}"
    assert result.title == "Search results"
    assert result.children

    for obj, child in zip(object_details, result.children, strict=False):
        assert isinstance(child, BrowseMediaSource)
        assert child.identifier == f"{MOCK_SOURCE_ID}/:{obj[0]}"
        assert child.title == obj[1]
        assert not child.children