async def test_timeout_cancelled(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    fakeimgbytes_png: bytes,
    fakeimgbytes_jpg: bytes,
) -> None:
    """Test that timeouts and cancellations return last image."""

    respx.get("http://example.com").respond(stream=fakeimgbytes_png)

    options = {
        "name": "config_test",
        "platform": "generic",
        "still_image_url": "http://example.com",
        "username": "user",
        "password": "pass",
        "framerate": 20,
    }
    await help_setup_mock_config_entry(hass, options)

    client = await hass_client()

    resp = await client.get("/api/camera_proxy/camera.config_test")

    assert resp.status == HTTPStatus.OK
    assert respx.calls.call_count == 1
    assert await resp.read() == fakeimgbytes_png

    respx.get("http://example.com").respond(stream=fakeimgbytes_jpg)

    with patch(
        "homeassistant.components.generic.camera.GenericCamera.async_camera_image",
        side_effect=asyncio.CancelledError(),
    ):
        resp = await client.get("/api/camera_proxy/camera.config_test")
        assert respx.calls.call_count == 1
        assert resp.status == HTTPStatus.INTERNAL_SERVER_ERROR

    respx.get("http://example.com").side_effect = [
        httpx.RequestError,
        httpx.TimeoutException,
    ]

    for total_calls in range(2, 4):
        # sleep .1 seconds to make cached image expire
        await asyncio.sleep(0.1)
        resp = await client.get("/api/camera_proxy/camera.config_test")
        assert respx.calls.call_count == total_calls
        assert resp.status == HTTPStatus.OK
        assert await resp.read() == fakeimgbytes_png