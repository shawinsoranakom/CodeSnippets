def test_post_items(client: TestClient):
    response = client.post(
        "/items/",
        json={
            "name": "Foo",
            "description": "Item description",
            "price": 42.0,
            "tax": 3.2,
            "tags": ["bar", "baz"],
        },
    )
    assert response.status_code == 201, response.text
    assert response.json() == {
        "name": "Foo",
        "description": "Item description",
        "price": 42.0,
        "tax": 3.2,
        "tags": IsList("bar", "baz", check_order=False),
    }