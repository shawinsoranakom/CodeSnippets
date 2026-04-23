async def test_fetching_url(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    fakeimgbytes_png: bytes,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that it fetches the given url."""
    hass.states.async_set("sensor.temp", "http://example.com/0a")
    respx.get("http://example.com/0a").respond(stream=fakeimgbytes_png)
    respx.get("http://example.com/1a").respond(stream=fakeimgbytes_png)

    options = {
        "name": "config_test",
        "platform": "generic",
        "still_image_url": "{{ states.sensor.temp.state }}",
        "username": "user",
        "password": "pass",
        "authentication": "basic",
        "framerate": 20,
    }
    await help_setup_mock_config_entry(hass, options)

    client = await hass_client()

    resp = await client.get("/api/camera_proxy/camera.config_test")

    assert resp.status == HTTPStatus.OK
    assert respx.calls.call_count == 1
    body = await resp.read()
    assert body == fakeimgbytes_png

    # sleep .1 seconds to make cached image expire
    await asyncio.sleep(0.1)

    resp = await client.get("/api/camera_proxy/camera.config_test")
    assert respx.calls.call_count == 2

    # If the template renders to an invalid URL we return the last image from cache
    hass.states.async_set("sensor.temp", "invalid url")

    # sleep another .1 seconds to make cached image expire
    await asyncio.sleep(0.1)
    resp = await client.get("/api/camera_proxy/camera.config_test")
    assert resp.status == HTTPStatus.OK
    assert respx.calls.call_count == 2
    assert (
        "Invalid URL 'invalid url': expected a URL, returning last image" in caplog.text
    )

    # Restore a valid URL
    hass.states.async_set("sensor.temp", "http://example.com/1a")
    await asyncio.sleep(0.1)
    resp = await client.get("/api/camera_proxy/camera.config_test")
    assert resp.status == HTTPStatus.OK
    assert respx.calls.call_count == 3