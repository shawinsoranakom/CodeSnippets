def test_path_operation(client: TestClient):
    response = client.get("/items/foo")
    assert response.status_code == 200, response.text
    assert response.json() == {"id": "foo", "value": "there goes my hero"}