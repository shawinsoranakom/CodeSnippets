def test_read_items_non_int_item_id(client: TestClient):
    response = client.get("/items/invalid_id?q=somequery")
    assert response.status_code == 422, response.text
    assert response.json() == {
        "detail": [
            {
                "loc": ["path", "item_id"],
                "input": "invalid_id",
                "msg": "Input should be a valid integer, unable to parse string as an integer",
                "type": "int_parsing",
            }
        ]
    }