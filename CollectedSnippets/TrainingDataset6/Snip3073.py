def test_path_param_le_ge_int_2_7():
    response = client.get("/path/param-le-ge-int/2.7")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "int_parsing",
                "loc": ["path", "item_id"],
                "msg": "Input should be a valid integer, unable to parse string as an integer",
                "input": "2.7",
            }
        ]
    }