async def test_fetch_image_authenticated(
    hass: HomeAssistant, hass_client: ClientSessionGenerator, mock_image_platform: None
) -> None:
    """Test fetching an image with an authenticated client."""
    client = await hass_client()

    # Using HEAD
    resp = await client.head("/api/image_proxy/image.test")
    assert resp.status == HTTPStatus.OK
    assert resp.content_type == "image/jpeg"
    assert resp.content_length == 4

    resp = await client.head("/api/image_proxy/image.unknown")
    assert resp.status == HTTPStatus.NOT_FOUND

    # Using GET
    resp = await client.get("/api/image_proxy/image.test")
    assert resp.status == HTTPStatus.OK
    body = await resp.read()
    assert body == b"Test"
    assert resp.content_type == "image/jpeg"
    assert resp.content_length == 4

    resp = await client.get("/api/image_proxy/image.unknown")
    assert resp.status == HTTPStatus.NOT_FOUND