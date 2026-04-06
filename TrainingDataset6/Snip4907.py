def test_read_items_item_id_less_than_one(client: TestClient):
    response = client.get("/items/0?q=somequery")
    assert response.status_code == 422, response.text
    assert response.json() == {
        "detail": [
            {
                "loc": ["path", "item_id"],
                "input": "0",
                "msg": "Input should be greater than or equal to 1",
                "type": "greater_than_equal",
                "ctx": {"ge": 1},
            }
        ]
    }