async def test_browse_media_get_albums(
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
    item = MediaSourceItem(hass, DOMAIN, "mocked_syno_dsm_entry", None)
    result = await source.async_browse_media(item)

    assert result
    assert len(result.children) == 3
    assert isinstance(result.children[0], BrowseMedia)
    assert result.children[0].identifier == "mocked_syno_dsm_entry/0"
    assert result.children[0].title == "All images"
    assert isinstance(result.children[1], BrowseMedia)
    assert result.children[1].identifier == "mocked_syno_dsm_entry/shared"
    assert result.children[1].title == "Shared space"
    assert isinstance(result.children[2], BrowseMedia)
    assert result.children[2].identifier == "mocked_syno_dsm_entry/1_"
    assert result.children[2].title == "Album 1"