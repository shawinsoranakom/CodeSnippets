async def test_camera_content_type(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    fakeimgbytes_svg: bytes,
    fakeimgbytes_jpg: bytes,
) -> None:
    """Test generic camera with custom content_type."""
    urlsvg = "https://upload.wikimedia.org/wikipedia/commons/0/02/SVG_logo.svg"
    respx.get(urlsvg).respond(stream=fakeimgbytes_svg)
    urljpg = "https://upload.wikimedia.org/wikipedia/commons/0/0e/Felis_silvestris_silvestris.jpg"
    respx.get(urljpg).respond(stream=fakeimgbytes_jpg)
    cam_config_svg = {
        "name": "config_test_svg",
        "platform": "generic",
        "still_image_url": urlsvg,
        "content_type": "image/svg+xml",
        "limit_refetch_to_url_change": False,
        "framerate": 2,
        "verify_ssl": True,
    }
    cam_config_jpg = {
        "name": "config_test_jpg",
        "platform": "generic",
        "still_image_url": urljpg,
        "content_type": "image/jpeg",
        "limit_refetch_to_url_change": False,
        "framerate": 2,
        "verify_ssl": True,
    }
    await help_setup_mock_config_entry(hass, cam_config_jpg, unique_id=12345)
    await help_setup_mock_config_entry(hass, cam_config_svg, unique_id=54321)

    client = await hass_client()

    resp_1 = await client.get("/api/camera_proxy/camera.config_test_svg")
    assert respx.calls.call_count == 1
    assert resp_1.status == HTTPStatus.OK
    assert resp_1.content_type == "image/svg+xml"
    body = await resp_1.read()
    assert body == fakeimgbytes_svg

    resp_2 = await client.get("/api/camera_proxy/camera.config_test_jpg")
    assert respx.calls.call_count == 2
    assert resp_2.status == HTTPStatus.OK
    assert resp_2.content_type == "image/jpeg"
    body = await resp_2.read()
    assert body == fakeimgbytes_jpg