def test_path_int_foobar():
    response = client.get("/path/int/foobar")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "int_parsing",
                "loc": ["path", "item_id"],
                "msg": "Input should be a valid integer, unable to parse string as an integer",
                "input": "foobar",
            }
        ]
    }