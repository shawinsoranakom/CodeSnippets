async def test_static_path_cache(mock_http_client: TestClient) -> None:
    """Test static paths cache."""
    resp = await mock_http_client.get("/lovelace/default_view", allow_redirects=False)
    assert resp.status == 404

    resp = await mock_http_client.get("/frontend_latest/", allow_redirects=False)
    assert resp.status == 403

    resp = await mock_http_client.get(
        "/static/icons/favicon.ico", allow_redirects=False
    )
    assert resp.status == 200

    # and again to make sure the cache works
    resp = await mock_http_client.get(
        "/static/icons/favicon.ico", allow_redirects=False
    )
    assert resp.status == 200

    resp = await mock_http_client.get(
        "/static/fonts/roboto/Roboto-Bold.woff2", allow_redirects=False
    )
    assert resp.status == 200

    resp = await mock_http_client.get("/static/does-not-exist", allow_redirects=False)
    assert resp.status == 404

    # and again to make sure the cache works
    resp = await mock_http_client.get("/static/does-not-exist", allow_redirects=False)
    assert resp.status == 404