async def test_resolve_media_object(hass: HomeAssistant, dms_device_mock: Mock) -> None:
    """Test the async_resolve_object method via async_resolve_media."""
    object_id: Final = "123"
    res_url: Final = "foo/bar"
    res_abs_url: Final = f"{MOCK_DEVICE_BASE_URL}/{res_url}"
    res_mime: Final = "audio/mpeg"
    # Success case: one resource
    didl_item = didl_lite.Item(
        id=object_id,
        restricted="false",
        title="Object",
        res=[didl_lite.Resource(uri=res_url, protocol_info=f"http-get:*:{res_mime}:")],
    )
    dms_device_mock.async_browse_metadata.return_value = didl_item
    result = await async_resolve_media(hass, f":{object_id}")
    dms_device_mock.async_browse_metadata.assert_awaited_once_with(
        object_id, metadata_filter="*"
    )
    assert result.url == res_abs_url
    assert result.mime_type == res_mime
    assert result.didl_metadata is didl_item

    # Success case: two resources, first is playable
    didl_item = didl_lite.Item(
        id=object_id,
        restricted="false",
        title="Object",
        res=[
            didl_lite.Resource(uri=res_url, protocol_info=f"http-get:*:{res_mime}:"),
            didl_lite.Resource(
                uri="thumbnail.png", protocol_info="http-get:*:image/png:"
            ),
        ],
    )
    dms_device_mock.async_browse_metadata.return_value = didl_item
    result = await async_resolve_media(hass, f":{object_id}")
    assert result.url == res_abs_url
    assert result.mime_type == res_mime
    assert result.didl_metadata is didl_item

    # Success case: three resources, only third is playable
    didl_item = didl_lite.Item(
        id=object_id,
        restricted="false",
        title="Object",
        res=[
            didl_lite.Resource(uri="", protocol_info=""),
            didl_lite.Resource(uri="internal:thing", protocol_info="internal:*::"),
            didl_lite.Resource(uri=res_url, protocol_info=f"http-get:*:{res_mime}:"),
        ],
    )
    dms_device_mock.async_browse_metadata.return_value = didl_item
    result = await async_resolve_media(hass, f":{object_id}")
    assert result.url == res_abs_url
    assert result.mime_type == res_mime
    assert result.didl_metadata is didl_item

    # Failure case: no resources
    didl_item = didl_lite.Item(
        id=object_id,
        restricted="false",
        title="Object",
        res=[],
    )
    dms_device_mock.async_browse_metadata.return_value = didl_item
    with pytest.raises(Unresolvable, match="Object has no resources"):
        await async_resolve_media(hass, f":{object_id}")

    # Failure case: resources are not playable
    didl_item = didl_lite.Item(
        id=object_id,
        restricted="false",
        title="Object",
        res=[didl_lite.Resource(uri="internal:thing", protocol_info="internal:*::")],
    )
    dms_device_mock.async_browse_metadata.return_value = didl_item
    with pytest.raises(Unresolvable, match="Object has no playable resources"):
        await async_resolve_media(hass, f":{object_id}")