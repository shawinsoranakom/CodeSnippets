async def test_browse_media_get_items(
    hass: HomeAssistant, dsm_with_photos: MagicMock
) -> None:
    """Test browse_media returning albums."""
    with (
        patch(
            "homeassistant.components.synology_dsm.common.SynologyDSM",
            return_value=dsm_with_photos,
        ),
        patch("homeassistant.components.synology_dsm.PLATFORMS", return_value=[]),
    ):
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_HOST: HOST,
                CONF_PORT: PORT,
                CONF_SSL: USE_SSL,
                CONF_USERNAME: USERNAME,
                CONF_PASSWORD: PASSWORD,
                CONF_MAC: MACS[0],
            },
            unique_id="mocked_syno_dsm_entry",
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)

    source = await async_get_media_source(hass)

    item = MediaSourceItem(hass, DOMAIN, "mocked_syno_dsm_entry/1", None)
    result = await source.async_browse_media(item)

    assert result
    assert len(result.children) == 2
    item = result.children[0]
    assert isinstance(item, BrowseMedia)
    assert item.identifier == "mocked_syno_dsm_entry/1_/10_1298753/filename.jpg"
    assert item.title == "filename.jpg"
    assert item.media_class == MediaClass.IMAGE
    assert item.media_content_type == "image/jpeg"
    assert item.can_play
    assert not item.can_expand
    assert item.thumbnail == "http://my.thumbnail.url"
    item = result.children[1]
    assert isinstance(item, BrowseMedia)
    assert item.identifier == "mocked_syno_dsm_entry/1_/10_1298753/filename.jpg_shared"
    assert item.title == "filename.jpg"
    assert item.media_class == MediaClass.IMAGE
    assert item.media_content_type == "image/jpeg"
    assert item.can_play
    assert not item.can_expand
    assert item.thumbnail == "http://my.thumbnail.url"

    item = MediaSourceItem(hass, DOMAIN, "mocked_syno_dsm_entry/shared", None)
    result = await source.async_browse_media(item)
    assert result
    assert len(result.children) == 1
    item = result.children[0]
    assert (
        item.identifier
        == "mocked_syno_dsm_entry/shared_/10_1298753/filename.jpg_shared"
    )
    assert item.title == "filename.jpg"
    assert item.media_class == MediaClass.IMAGE
    assert item.media_content_type == "image/jpeg"
    assert item.can_play
    assert not item.can_expand
    assert item.thumbnail == "http://my.thumbnail.url"