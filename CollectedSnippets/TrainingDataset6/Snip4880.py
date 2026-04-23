def test_get_items_invalid_id():
    response = client.get("/items/item1")
    assert response.status_code == 422, response.text
    assert response.json() == {
        "detail": [
            {
                "input": "item1",
                "loc": ["path", "item_id"],
                "msg": "Input should be a valid integer, unable to parse string as an integer",
                "type": "int_parsing",
            }
        ]
    }