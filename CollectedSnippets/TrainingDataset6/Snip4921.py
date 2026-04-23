def test_read_items_size_too_small(client: TestClient):
    response = client.get("/items/1?q=somequery&size=0.0")
    assert response.status_code == 422, response.text
    assert response.json() == {
        "detail": [
            {
                "loc": ["query", "size"],
                "input": "0.0",
                "msg": "Input should be greater than 0",
                "type": "greater_than",
                "ctx": {"gt": 0.0},
            }
        ]
    }