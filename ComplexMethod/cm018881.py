async def test_media_view(
    hass: HomeAssistant, hass_client: ClientSessionGenerator
) -> None:
    """Test media view."""
    local_media = hass.config.path("media")
    await async_process_ha_core_config(
        hass, {"media_dirs": {"local": local_media, "recordings": local_media}}
    )
    await hass.async_block_till_done()

    assert await async_setup_component(hass, const.DOMAIN, {})
    await hass.async_block_till_done()

    client = await hass_client()

    # Protects against non-existent files
    resp = await client.head("/media/local/invalid.txt")
    assert resp.status == HTTPStatus.NOT_FOUND

    resp = await client.get("/media/local/invalid.txt")
    assert resp.status == HTTPStatus.NOT_FOUND

    resp = await client.get("/media/recordings/invalid.txt")
    assert resp.status == HTTPStatus.NOT_FOUND

    # Protects against non-media files
    resp = await client.head("/media/local/not_media.txt")
    assert resp.status == HTTPStatus.NOT_FOUND

    resp = await client.get("/media/local/not_media.txt")
    assert resp.status == HTTPStatus.NOT_FOUND

    # Protects against unknown local media sources
    resp = await client.head("/media/unknown_source/not_media.txt")
    assert resp.status == HTTPStatus.NOT_FOUND

    resp = await client.get("/media/unknown_source/not_media.txt")
    assert resp.status == HTTPStatus.NOT_FOUND

    # Fetch available media
    resp = await client.head("/media/local/test.mp3")
    assert resp.status == HTTPStatus.OK
    assert resp.content_type == "audio/mpeg"

    resp = await client.get("/media/local/test.mp3")
    assert resp.status == HTTPStatus.OK

    resp = await client.head("/media/local/Epic Sax Guy 10 Hours.mp4")
    assert resp.status == HTTPStatus.OK
    assert resp.content_type == "video/mp4"

    resp = await client.get("/media/local/Epic Sax Guy 10 Hours.mp4")
    assert resp.status == HTTPStatus.OK

    resp = await client.get("/media/recordings/test.mp3")
    assert resp.status == HTTPStatus.OK