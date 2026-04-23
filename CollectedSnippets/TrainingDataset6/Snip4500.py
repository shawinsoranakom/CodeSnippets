def test_post_id_foo(client: TestClient):
    response = client.put(
        "/items/foo",
        json={
            "item": {"name": "Foo", "price": 50.5},
            "user": {"username": "johndoe"},
        },
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "int_parsing",
                "loc": ["path", "item_id"],
                "msg": "Input should be a valid integer, unable to parse string as an integer",
                "input": "foo",
            }
        ]
    }