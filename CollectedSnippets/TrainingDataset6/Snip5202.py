def test_incorrect_token(mod: ModuleType):
    client = TestClient(mod.app)
    response = client.get("/users/me", headers={"Authorization": "Bearer nonexistent"})
    assert response.status_code == 401, response.text
    assert response.json() == {"detail": "Could not validate credentials"}
    assert response.headers["WWW-Authenticate"] == "Bearer"