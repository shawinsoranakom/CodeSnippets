def test_put_only_required(client: TestClient):
    response = client.put(
        "/items/5",
        json={
            "importance": 2,
            "item": {"name": "Foo", "price": 50.5},
            "user": {"username": "Dave"},
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "item_id": 5,
        "importance": 2,
        "item": {
            "name": "Foo",
            "price": 50.5,
            "description": None,
            "tax": None,
        },
        "user": {"username": "Dave", "full_name": None},
    }