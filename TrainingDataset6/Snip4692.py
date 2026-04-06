def test_get(mod: ModuleType):
    client = TestClient(mod.app)
    response = client.get("/items/plumbus")
    assert response.status_code == 200, response.text
    assert response.json() == "plumbus"