def test_read_items_item_id_greater_than_one_thousand(client: TestClient):
    response = client.get("/items/1001?q=somequery&size=5")
    assert response.status_code == 422, response.text
    assert response.json() == {
        "detail": [
            {
                "loc": ["path", "item_id"],
                "input": "1001",
                "msg": "Input should be less than or equal to 1000",
                "type": "less_than_equal",
                "ctx": {"le": 1000},
            }
        ]
    }