def test_login(mod: ModuleType):
    client = TestClient(mod.app)
    response = client.post("/token", data={"username": "johndoe", "password": "secret"})
    assert response.status_code == 200, response.text
    content = response.json()
    assert "access_token" in content
    assert content["token_type"] == "bearer"