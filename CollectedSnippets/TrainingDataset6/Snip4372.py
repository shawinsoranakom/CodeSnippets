def test_get_root_no_token():
    response = client.get("/")
    assert response.status_code == 401, response.text
    assert response.json() == {"detail": "Not authenticated"}