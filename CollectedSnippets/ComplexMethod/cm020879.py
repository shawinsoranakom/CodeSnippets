async def test_limit_refetch(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    fakeimgbytes_png: bytes,
    fakeimgbytes_jpg: bytes,
) -> None:
    """Test that it fetches the given url."""
    respx.get("http://example.com/0a").respond(stream=fakeimgbytes_png)
    respx.get("http://example.com/5a").respond(stream=fakeimgbytes_png)
    respx.get("http://example.com/10a").respond(stream=fakeimgbytes_png)
    respx.get("http://example.com/15a").respond(stream=fakeimgbytes_jpg)
    respx.get("http://example.com/20a").respond(status_code=HTTPStatus.NOT_FOUND)

    hass.states.async_set("sensor.temp", "0")

    options = {
        "name": "config_test",
        "platform": "generic",
        "still_image_url": 'http://example.com/{{ states.sensor.temp.state + "a" }}',
        "limit_refetch_to_url_change": True,
    }
    await help_setup_mock_config_entry(hass, options)

    client = await hass_client()

    resp = await client.get("/api/camera_proxy/camera.config_test")

    hass.states.async_set("sensor.temp", "5")

    with (
        pytest.raises(aiohttp.ServerTimeoutError),
        patch.object(
            client.session._connector, "connect", side_effect=asyncio.TimeoutError
        ),
    ):
        resp = await client.get("/api/camera_proxy/camera.config_test")

    assert respx.calls.call_count == 1
    assert resp.status == HTTPStatus.OK

    hass.states.async_set("sensor.temp", "10")

    resp = await client.get("/api/camera_proxy/camera.config_test")
    assert respx.calls.call_count == 2
    assert resp.status == HTTPStatus.OK
    body = await resp.read()
    assert body == fakeimgbytes_png

    resp = await client.get("/api/camera_proxy/camera.config_test")
    assert respx.calls.call_count == 2
    assert resp.status == HTTPStatus.OK
    body = await resp.read()
    assert body == fakeimgbytes_png

    hass.states.async_set("sensor.temp", "15")

    # Url change = fetch new image
    resp = await client.get("/api/camera_proxy/camera.config_test")
    assert respx.calls.call_count == 3
    assert resp.status == HTTPStatus.OK
    body = await resp.read()
    assert body == fakeimgbytes_jpg

    # Cause a template render error
    hass.states.async_remove("sensor.temp")
    resp = await client.get("/api/camera_proxy/camera.config_test")
    assert respx.calls.call_count == 3
    assert resp.status == HTTPStatus.OK
    body = await resp.read()
    assert body == fakeimgbytes_jpg