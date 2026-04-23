async def test_resolve_media_search(hass: HomeAssistant, dms_device_mock: Mock) -> None:
    """Test the async_resolve_search method via async_resolve_media."""
    res_url: Final = "foo/bar"
    res_abs_url: Final = f"{MOCK_DEVICE_BASE_URL}/{res_url}"
    res_mime: Final = "audio/mpeg"

    # No results
    dms_device_mock.async_search_directory.return_value = DmsDevice.BrowseResult(
        [], 0, 0, 0
    )
    with pytest.raises(Unresolvable, match='Nothing found for dc:title="thing"'):
        await async_resolve_media(hass, '?dc:title="thing"')
    assert dms_device_mock.async_search_directory.await_args_list == [
        call(
            container_id="0",
            search_criteria='dc:title="thing"',
            metadata_filter="*",
            requested_count=1,
        )
    ]

    # One result
    dms_device_mock.async_search_directory.reset_mock()
    didl_item = didl_lite.Item(
        id="thing's id",
        restricted="false",
        title="thing",
        res=[didl_lite.Resource(uri=res_url, protocol_info=f"http-get:*:{res_mime}:")],
    )
    dms_device_mock.async_search_directory.return_value = DmsDevice.BrowseResult(
        [didl_item], 1, 1, 0
    )
    result = await async_resolve_media(hass, '?dc:title="thing"')
    assert result.url == res_abs_url
    assert result.mime_type == res_mime
    assert result.didl_metadata is didl_item
    assert dms_device_mock.async_search_directory.await_count == 1
    # Values should be taken from search result, not querying the item's metadata
    assert dms_device_mock.async_browse_metadata.await_count == 0

    # Two results - uses the first
    dms_device_mock.async_search_directory.return_value = DmsDevice.BrowseResult(
        [didl_item], 1, 2, 0
    )
    result = await async_resolve_media(hass, '?dc:title="thing"')
    assert result.url == res_abs_url
    assert result.mime_type == res_mime
    assert result.didl_metadata is didl_item

    # Bad result
    dms_device_mock.async_search_directory.return_value = DmsDevice.BrowseResult(
        [didl_lite.Descriptor("id", "namespace")], 1, 1, 0
    )
    with pytest.raises(Unresolvable, match="Descriptor.* is not a DidlObject"):
        await async_resolve_media(hass, '?dc:title="thing"')