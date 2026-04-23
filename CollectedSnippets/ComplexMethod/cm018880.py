async def test_async_browse_media(hass: HomeAssistant) -> None:
    """Test browse media."""
    local_media = hass.config.path("media")
    await async_process_ha_core_config(
        hass, {"media_dirs": {"local": local_media, "recordings": local_media}}
    )
    await hass.async_block_till_done()

    assert await async_setup_component(hass, const.DOMAIN, {})
    await hass.async_block_till_done()

    # Test path not exists
    with pytest.raises(BrowseError) as excinfo:
        await media_source.async_browse_media(
            hass, f"{const.URI_SCHEME}{const.DOMAIN}/local/test/not/exist"
        )
    assert str(excinfo.value) == "Path does not exist."

    # Test browse file
    with pytest.raises(BrowseError) as excinfo:
        await media_source.async_browse_media(
            hass, f"{const.URI_SCHEME}{const.DOMAIN}/local/test.mp3"
        )
    assert str(excinfo.value) == "Path is not a directory."

    # Test invalid base
    with pytest.raises(BrowseError) as excinfo:
        await media_source.async_browse_media(
            hass, f"{const.URI_SCHEME}{const.DOMAIN}/invalid/base"
        )
    assert str(excinfo.value) == "Unknown source directory."

    # Test directory traversal
    with pytest.raises(BrowseError) as excinfo:
        await media_source.async_browse_media(
            hass, f"{const.URI_SCHEME}{const.DOMAIN}/local/../configuration.yaml"
        )
    assert str(excinfo.value) == "Invalid path."

    # Test successful listing
    media = await media_source.async_browse_media(
        hass, f"{const.URI_SCHEME}{const.DOMAIN}"
    )
    assert media

    media = await media_source.async_browse_media(
        hass, f"{const.URI_SCHEME}{const.DOMAIN}/local/."
    )
    assert media

    media = await media_source.async_browse_media(
        hass, f"{const.URI_SCHEME}{const.DOMAIN}/recordings/."
    )
    assert media