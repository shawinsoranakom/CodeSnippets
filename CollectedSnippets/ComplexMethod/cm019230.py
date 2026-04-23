async def test_browse_media_collections(
    hass: HomeAssistant,
    mock_immich: Mock,
    mock_config_entry: MockConfigEntry,
    collection: str,
    children: list[dict],
) -> None:
    """Test browse through collections."""
    assert await async_setup_component(hass, "media_source", {})

    with patch("homeassistant.components.immich.PLATFORMS", []):
        await setup_integration(hass, mock_config_entry)

    source = await async_get_media_source(hass)
    item = MediaSourceItem(
        hass, DOMAIN, f"{mock_config_entry.unique_id}|{collection}", None
    )
    result = await source.async_browse_media(item)

    assert result
    assert len(result.children) == len(children)
    for idx, child in enumerate(children):
        media_file = result.children[idx]
        assert isinstance(media_file, BrowseMedia)
        assert media_file.title == child["title"]
        assert media_file.media_content_id == (
            "media-source://immich/"
            f"{mock_config_entry.unique_id}|{collection}|"
            f"{child['asset_id']}"
        )