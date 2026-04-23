def test_get_invalid():
    response = client.get("/foo")
    assert response.status_code == 422