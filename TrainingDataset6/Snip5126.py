def test_create_item_only_required(client: TestClient):
    response = client.post(
        "/items/",
        json={
            "name": "Test Item",
            "price": 10.5,
        },
    )
    assert response.status_code == 200, response.text
    assert response.json() == {
        "name": "Test Item",
        "price": 10.5,
        "description": None,
        "tax": None,
        "tags": [],
    }