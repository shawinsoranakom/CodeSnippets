def test_create_item(client: TestClient):
    item_data = {
        "name": "Test Item",
        "description": "A test item",
        "price": 10.5,
        "tax": 1.5,
        "tags": ["test", "item"],
    }
    response = client.post("/items/", json=item_data)
    assert response.status_code == 200, response.text
    assert response.json() == item_data