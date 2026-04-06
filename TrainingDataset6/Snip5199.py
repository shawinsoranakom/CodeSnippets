def test_login_incorrect_username(mod: ModuleType):
    client = TestClient(mod.app)
    response = client.post("/token", data={"username": "foo", "password": "secret"})
    assert response.status_code == 401, response.text
    assert response.json() == {"detail": "Incorrect username or password"}