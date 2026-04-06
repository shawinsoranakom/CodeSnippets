def test_put_only_required(client: TestClient):
    response = client.put(
        "/items/123",
        json={"name": "Foo", "price": 50.1},
    )
    assert response.status_code == 200
    assert response.json() == {
        "item_id": 123,
        "name": "Foo",
        "price": 50.1,
        "description": None,
        "tax": None,
    }