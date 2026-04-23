def test_post_all(client: TestClient):
    response = client.put(
        "/items/5",
        json={
            "item": {
                "name": "Foo",
                "price": 50.5,
                "description": "Some Foo",
                "tax": 0.1,
            },
            "user": {"username": "johndoe", "full_name": "John Doe"},
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "item_id": 5,
        "item": {
            "name": "Foo",
            "price": 50.5,
            "description": "Some Foo",
            "tax": 0.1,
        },
        "user": {"username": "johndoe", "full_name": "John Doe"},
    }