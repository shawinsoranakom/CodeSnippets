def test_post_missing_required_field_in_item(client: TestClient):
    response = client.put(
        "/items/5", json={"item": {"name": "Foo"}, "user": {"username": "johndoe"}}
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "input": {"name": "Foo"},
                "loc": [
                    "body",
                    "item",
                    "price",
                ],
                "msg": "Field required",
                "type": "missing",
            },
        ],
    }