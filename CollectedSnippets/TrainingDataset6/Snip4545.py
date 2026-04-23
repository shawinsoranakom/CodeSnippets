def test_put_only_required(client: TestClient):
    response = client.put(
        "/items/5",
        json={"name": "Foo", "price": 35.4},
    )
    assert response.status_code == 200, response.text
    assert response.json() == {
        "item_id": 5,
        "item": {
            "name": "Foo",
            "description": None,
            "price": 35.4,
            "tax": None,
            "tags": [],
            "images": None,
        },
    }