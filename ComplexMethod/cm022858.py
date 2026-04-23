async def test_fetch_image_url_success(
    hass: HomeAssistant, hass_client: ClientSessionGenerator
) -> None:
    """Test fetching an image with an authenticated client."""
    respx.get("https://example.com/myimage.jpg").respond(
        status_code=HTTPStatus.OK, content_type="image/png", content=b"Test"
    )

    mock_integration(hass, MockModule(domain="test"))
    mock_platform(hass, "test.image", MockImagePlatform([MockURLImageEntity(hass)]))
    assert await async_setup_component(
        hass, image.DOMAIN, {"image": {"platform": "test"}}
    )
    await hass.async_block_till_done()

    client = await hass_client()

    # Using HEAD
    resp = await client.head("/api/image_proxy/image.test")
    assert resp.status == HTTPStatus.OK
    assert resp.content_type == "image/png"
    assert resp.content_length == 4

    # Using GET
    resp = await client.get("/api/image_proxy/image.test")
    assert resp.status == HTTPStatus.OK
    body = await resp.read()
    assert body == b"Test"
    assert resp.content_type == "image/png"
    assert resp.content_length == 4