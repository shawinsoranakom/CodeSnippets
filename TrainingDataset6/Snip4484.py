def test_invalid_price(client: TestClient):
    response = client.put("/items/5", json={"item": {"name": "Foo", "price": -3.0}})
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "greater_than",
                "loc": ["body", "item", "price"],
                "msg": "Input should be greater than 0",
                "input": -3.0,
                "ctx": {"gt": 0.0},
            }
        ]
    }