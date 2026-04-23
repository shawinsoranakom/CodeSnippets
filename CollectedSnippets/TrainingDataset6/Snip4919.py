def test_read_items_item_id_less_than_zero(client: TestClient):
    response = client.get("/items/-1?q=somequery&size=5")
    assert response.status_code == 422, response.text
    assert response.json() == {
        "detail": [
            {
                "loc": ["path", "item_id"],
                "input": "-1",
                "msg": "Input should be greater than or equal to 0",
                "type": "greater_than_equal",
                "ctx": {"ge": 0},
            }
        ]
    }