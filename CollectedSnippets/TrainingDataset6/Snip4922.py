def test_read_items_size_too_large(client: TestClient):
    response = client.get("/items/1?q=somequery&size=10.5")
    assert response.status_code == 422, response.text
    assert response.json() == {
        "detail": [
            {
                "loc": ["query", "size"],
                "input": "10.5",
                "msg": "Input should be less than 10.5",
                "type": "less_than",
                "ctx": {"lt": 10.5},
            }
        ]
    }