def test_path_int_True():
    response = client.get("/path/int/True")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "int_parsing",
                "loc": ["path", "item_id"],
                "msg": "Input should be a valid integer, unable to parse string as an integer",
                "input": "True",
            }
        ]
    }