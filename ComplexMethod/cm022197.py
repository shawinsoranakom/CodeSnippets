async def test_browse_media_multiple_sources(
    hass: HomeAssistant, dms_device_mock: Mock, device_source_mock: None
) -> None:
    """Test browse_media without a source_id, with multiple devices registered."""
    # Set up a second source
    other_source_id = "second_source"
    other_source_title = "Second source"
    other_config_entry = MockConfigEntry(
        unique_id=f"different-udn::{MOCK_DEVICE_TYPE}",
        domain=DOMAIN,
        data={
            CONF_URL: "http://192.88.99.22/dms_description.xml",
            CONF_DEVICE_ID: f"different-udn::{MOCK_DEVICE_TYPE}",
        },
        title=other_source_title,
    )
    other_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(other_config_entry.entry_id)
    await hass.async_block_till_done()

    # No source_id nor media_id
    result = await media_source.async_browse_media(hass, f"media-source://{DOMAIN}")
    # Mock device should not have been browsed
    assert dms_device_mock.async_browse_metadata.await_count == 0
    # Result will be a list of available devices
    assert result.title == "DLNA Servers"
    assert result.children
    assert isinstance(result.children[0], BrowseMediaSource)
    assert result.children[0].identifier == f"{MOCK_SOURCE_ID}/:0"
    assert result.children[0].title == MOCK_DEVICE_NAME
    assert result.children[0].thumbnail == dms_device_mock.icon
    assert isinstance(result.children[1], BrowseMediaSource)
    assert result.children[1].identifier == f"{other_source_id}/:0"
    assert result.children[1].title == other_source_title

    # No source_id but a media_id
    # media_source.URI_SCHEME_REGEX won't let the ID through to dlna_dms
    with pytest.raises(BrowseError, match="Invalid media source URI"):
        result = await media_source.async_browse_media(
            hass, f"media-source://{DOMAIN}//:media-item-id"
        )
    # Mock device should not have been browsed
    assert dms_device_mock.async_browse_metadata.await_count == 0

    # Clean up, to fulfil ssdp_scanner post-condition of every callback being cleared
    await hass.config_entries.async_remove(other_config_entry.entry_id)