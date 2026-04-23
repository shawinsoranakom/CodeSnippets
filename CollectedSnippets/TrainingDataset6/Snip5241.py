def test_security_http_basic(client: TestClient):
    response = client.get("/users/me", auth=("stanleyjobson", "swordfish"))
    assert response.status_code == 200, response.text
    assert response.json() == {"username": "stanleyjobson"}