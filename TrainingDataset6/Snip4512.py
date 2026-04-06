def test_put_invalid_importance(client: TestClient):
    response = client.put(
        "/items/5",
        json={
            "importance": 0,
            "item": {"name": "Foo", "price": 50.5},
            "user": {"username": "Dave"},
        },
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "loc": ["body", "importance"],
                "msg": "Input should be greater than 0",
                "type": "greater_than",
                "input": 0,
                "ctx": {"gt": 0},
            },
        ],
    }