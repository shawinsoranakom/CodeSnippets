def test_get_credentials():
    response = client.get("/get-credentials", headers={"authorization": "Bearer token"})
    assert response.status_code == 200, response.text
    assert response.json() == {"token": "token", "scopes": ["a", "b"]}