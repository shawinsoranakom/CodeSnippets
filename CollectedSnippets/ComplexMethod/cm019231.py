async def test_browse_media_collection_get_items(
    hass: HomeAssistant,
    mock_immich: Mock,
    mock_config_entry: MockConfigEntry,
    collection: str,
    collection_id: str,
    children: list[dict],
) -> None:
    """Test browse_media returning albums."""
    assert await async_setup_component(hass, "media_source", {})

    with patch("homeassistant.components.immich.PLATFORMS", []):
        await setup_integration(hass, mock_config_entry)

    source = await async_get_media_source(hass)

    item = MediaSourceItem(
        hass,
        DOMAIN,
        f"{mock_config_entry.unique_id}|{collection}|{collection_id}",
        None,
    )
    result = await source.async_browse_media(item)

    assert result
    assert len(result.children) == len(children)

    for idx, child in enumerate(children):
        media_file = result.children[idx]
        assert isinstance(media_file, BrowseMedia)
        assert media_file.identifier == (
            f"{mock_config_entry.unique_id}|{collection}|{collection_id}|"
            f"{child['asset_id']}|{child['original_file_name']}|{child['media_content_type']}"
        )
        assert media_file.title == child["original_file_name"]
        assert media_file.media_class == child["media_class"]
        assert media_file.media_content_type == child["media_content_type"]
        assert media_file.can_play is child["can_play"]
        assert not media_file.can_expand
        assert media_file.thumbnail == (
            f"/immich/{mock_config_entry.unique_id}/"
            f"{child['asset_id']}/thumbnail/{child['thumb_mime_type']}"
        )