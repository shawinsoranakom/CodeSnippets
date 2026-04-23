async def test_headers_added(aiohttp_client: ClientSessionGenerator) -> None:
    """Test that headers are being added on each request."""
    app = web.Application()
    app.router.add_get("/", mock_handler)
    app.router.add_get("/error", mock_handler_error)

    setup_headers(app, use_x_frame_options=True)

    mock_api_client = await aiohttp_client(app)
    resp = await mock_api_client.get("/")

    assert resp.status == HTTPStatus.OK
    assert resp.headers["Referrer-Policy"] == "no-referrer"
    assert resp.headers["Server"] == ""
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "SAMEORIGIN"

    resp = await mock_api_client.get("/error")

    assert resp.status == HTTPStatus.UNAUTHORIZED
    assert resp.headers["Referrer-Policy"] == "no-referrer"
    assert resp.headers["Server"] == ""
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "SAMEORIGIN"