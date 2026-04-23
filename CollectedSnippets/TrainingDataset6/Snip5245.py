def test_security_http_basic_invalid_username(client: TestClient):
    response = client.get("/users/me", auth=("alice", "swordfish"))
    assert response.status_code == 401, response.text
    assert response.json() == {"detail": "Incorrect username or password"}
    assert response.headers["WWW-Authenticate"] == "Basic"