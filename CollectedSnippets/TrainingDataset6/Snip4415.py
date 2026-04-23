def test_redirect() -> None:
    response = client.get("/items")
    assert response.status_code == 307
    assert response.headers["location"] == "https://example.com/items/"