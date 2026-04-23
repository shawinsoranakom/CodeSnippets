async def test_browse_media_get_items_error(
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

    # unknown album
    dsm_with_photos.photos.get_items_from_album = AsyncMock(return_value=[])
    item = MediaSourceItem(hass, DOMAIN, "mocked_syno_dsm_entry/1", None)
    result = await source.async_browse_media(item)

    assert result
    assert result.identifier is None
    assert len(result.children) == 0

    # exception in get_items_from_album()
    dsm_with_photos.photos.get_items_from_album = AsyncMock(
        side_effect=SynologyDSMException("", None)
    )
    item = MediaSourceItem(hass, DOMAIN, "mocked_syno_dsm_entry/1", None)
    result = await source.async_browse_media(item)

    assert result
    assert result.identifier is None
    assert len(result.children) == 0

    # exception in get_items_from_shared_space()
    dsm_with_photos.photos.get_items_from_shared_space = AsyncMock(
        side_effect=SynologyDSMException("", None)
    )
    item = MediaSourceItem(hass, DOMAIN, "mocked_syno_dsm_entry/shared", None)
    result = await source.async_browse_media(item)

    assert result
    assert result.identifier is None
    assert len(result.children) == 0