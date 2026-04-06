def test_get_no_item(mod: ModuleType):
    client = TestClient(mod.app)
    response = client.get("/items/foo")
    assert response.status_code == 404, response.text
    assert response.json() == {"detail": "Item not found, there's only a plumbus here"}