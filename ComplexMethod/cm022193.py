async def test_resolve_media_path(hass: HomeAssistant, dms_device_mock: Mock) -> None:
    """Test the async_resolve_path method via async_resolve_media."""
    # Path resolution involves searching each component of the path, then
    # browsing the metadata of the final object found.
    path: Final = "path/to/thing"
    object_ids: Final = ["path_id", "to_id", "thing_id"]
    res_url: Final = "foo/bar"
    res_abs_url: Final = f"{MOCK_DEVICE_BASE_URL}/{res_url}"
    res_mime: Final = "audio/mpeg"

    search_directory_result = []
    for ob_id, ob_title in zip(object_ids, path.split("/"), strict=False):
        didl_item = didl_lite.Item(
            id=ob_id,
            restricted="false",
            title=ob_title,
            res=[],
        )
        search_directory_result.append(DmsDevice.BrowseResult([didl_item], 1, 1, 0))

    # Test that path is resolved correctly
    dms_device_mock.async_search_directory.side_effect = search_directory_result
    dms_device_mock.async_browse_metadata.return_value = didl_lite.Item(
        id=object_ids[-1],
        restricted="false",
        title="thing",
        res=[didl_lite.Resource(uri=res_url, protocol_info=f"http-get:*:{res_mime}:")],
    )
    result = await async_resolve_media(hass, f"/{path}")
    assert dms_device_mock.async_search_directory.await_args_list == [
        call(
            parent_id,
            search_criteria=f'@parentID="{parent_id}" and dc:title="{title}"',
            metadata_filter=["id", "upnp:class", "dc:title"],
            requested_count=1,
        )
        for parent_id, title in zip(
            ["0", *object_ids[:-1]], path.split("/"), strict=False
        )
    ]
    assert result.url == res_abs_url
    assert result.mime_type == res_mime

    # Test a path starting with a / (first / is path action, second / is root of path)
    dms_device_mock.async_search_directory.reset_mock()
    dms_device_mock.async_search_directory.side_effect = search_directory_result
    result = await async_resolve_media(hass, f"//{path}")
    assert dms_device_mock.async_search_directory.await_args_list == [
        call(
            parent_id,
            search_criteria=f'@parentID="{parent_id}" and dc:title="{title}"',
            metadata_filter=["id", "upnp:class", "dc:title"],
            requested_count=1,
        )
        for parent_id, title in zip(
            ["0", *object_ids[:-1]], path.split("/"), strict=False
        )
    ]
    assert result.url == res_abs_url
    assert result.mime_type == res_mime