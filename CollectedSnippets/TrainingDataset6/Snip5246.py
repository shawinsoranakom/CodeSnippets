def test_security_http_basic_invalid_password(client: TestClient):
    response = client.get("/users/me", auth=("stanleyjobson", "wrongpassword"))
    assert response.status_code == 401, response.text
    assert response.json() == {"detail": "Incorrect username or password"}
    assert response.headers["WWW-Authenticate"] == "Basic"