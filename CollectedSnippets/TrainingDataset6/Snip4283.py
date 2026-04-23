def test_no_keepalive_when_fast(client: TestClient):
    """No keepalive comment when items arrive quickly."""
    response = client.get("/items/stream")
    assert response.status_code == 200
    # KEEPALIVE_COMMENT is ": ping\n\n".
    assert ": ping\n" not in response.text