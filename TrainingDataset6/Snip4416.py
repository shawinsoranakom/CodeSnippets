def test_no_redirect() -> None:
    response = client.get("/items/")
    assert response.status_code == 200
    assert response.json() == ["plumbus", "portal gun"]