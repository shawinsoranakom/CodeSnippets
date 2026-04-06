def test_path_int_42_5():
    response = client.get("/path/int/42.5")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "int_parsing",
                "loc": ["path", "item_id"],
                "msg": "Input should be a valid integer, unable to parse string as an integer",
                "input": "42.5",
            }
        ]
    }