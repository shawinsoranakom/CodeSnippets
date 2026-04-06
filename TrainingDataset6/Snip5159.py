def test_create_item(client: TestClient):
    response = client.post("/items/", params={"name": "Test Item"})
    assert response.status_code == 201, response.text
    assert response.json() == {"name": "Test Item"}