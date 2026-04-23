def test_login_incorrect_password(mod: ModuleType):
    client = TestClient(mod.app)
    response = client.post(
        "/token", data={"username": "johndoe", "password": "incorrect"}
    )
    assert response.status_code == 401, response.text
    assert response.json() == {"detail": "Incorrect username or password"}