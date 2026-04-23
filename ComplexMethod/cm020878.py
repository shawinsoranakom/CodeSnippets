async def test_image_caching(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    freezer: FrozenDateTimeFactory,
    fakeimgbytes_png: bytes,
) -> None:
    """Test that the image is cached and not fetched more often than the framerate indicates."""
    respx.get("http://example.com").respond(stream=fakeimgbytes_png)

    framerate = 5
    options = {
        "name": "config_test",
        "platform": "generic",
        "still_image_url": "http://example.com",
        "username": "user",
        "password": "pass",
        "authentication": "basic",
        "framerate": framerate,
    }
    await help_setup_mock_config_entry(hass, options)

    client = await hass_client()

    resp = await client.get("/api/camera_proxy/camera.config_test")
    assert resp.status == HTTPStatus.OK
    body = await resp.read()
    assert body == fakeimgbytes_png

    resp = await client.get("/api/camera_proxy/camera.config_test")
    assert resp.status == HTTPStatus.OK
    body = await resp.read()
    assert body == fakeimgbytes_png

    # time is frozen, image should have come from cache
    assert respx.calls.call_count == 1

    # advance time by 150ms
    freezer.tick(timedelta(seconds=0.150))

    resp = await client.get("/api/camera_proxy/camera.config_test")
    assert resp.status == HTTPStatus.OK
    body = await resp.read()
    assert body == fakeimgbytes_png

    # Only 150ms have passed, image should still have come from cache
    assert respx.calls.call_count == 1

    # advance time by another 150ms
    freezer.tick(timedelta(seconds=0.150))

    resp = await client.get("/api/camera_proxy/camera.config_test")
    assert resp.status == HTTPStatus.OK
    body = await resp.read()
    assert body == fakeimgbytes_png

    # 300ms have passed, now we should have fetched a new image
    assert respx.calls.call_count == 2

    resp = await client.get("/api/camera_proxy/camera.config_test")
    assert resp.status == HTTPStatus.OK
    body = await resp.read()
    assert body == fakeimgbytes_png

    # Still only 300ms have passed, should have returned the cached image
    assert respx.calls.call_count == 2